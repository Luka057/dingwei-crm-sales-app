"""
Upload service — 拜访照片(Q7 决议:完整可用)。

实施细节(§11.1):
- 5MB 限(settings.upload_max_size_bytes)
- JPEG/PNG only — magic bytes 校验(python-magic),拒绝非真照片
- per-user 限速:小时 / 天(默认 30/100,O3 悬挂)
- 本地 docker volume:uploads/visits/{yyyymm}/{uuid}.jpg
- 文件名 UUID,防穷举

§3.5.4 边界 case #4 鉴权链路(get_visit_photo):
  attachment → visit_record.salesperson_id → user.manager_id == current_user.id
  OR uploader_id == current(orphan 阶段)

设计:visit_attachment.visit_record_id 可空 → 允许"先传图后绑表单"。
uploader_id NOT NULL → 任何时候都能查权限 + 限速。
"""

from __future__ import annotations

import uuid as uuid_lib
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import magic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User
from app.models.visit_attachment import AttachmentType, VisitAttachment
from app.models.visit_record import VisitRecord
from app.schemas.visit_record import VisitAttachmentOut

if TYPE_CHECKING:
    from app.core.deps import AuthUser


_MIME_TO_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
}


class UploadError(Exception):
    """业务级上传错误,调用方转 HTTP 4xx。"""

    def __init__(self, code: int, msg: str) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg


def _detect_mime(content: bytes) -> str:
    """magic bytes 校验,返回 mime type。不信任前端 content-type / 扩展名。"""
    return magic.from_buffer(content[:2048], mime=True)


async def _check_rate_limit(db: AsyncSession, uploader_id: UUID) -> None:
    """per-user 上传限速(基于 uploader_id,无论是否已绑 visit)。"""
    settings = get_settings()
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    last_hour = await db.scalar(
        select(func.count())
        .select_from(VisitAttachment)
        .where(
            VisitAttachment.uploader_id == uploader_id,
            VisitAttachment.uploaded_at >= hour_ago,
        )
    ) or 0
    if last_hour >= settings.upload_rate_limit_per_hour:
        raise UploadError(
            429,
            f"upload rate limit exceeded (per hour: {settings.upload_rate_limit_per_hour})",
        )

    last_day = await db.scalar(
        select(func.count())
        .select_from(VisitAttachment)
        .where(
            VisitAttachment.uploader_id == uploader_id,
            VisitAttachment.uploaded_at >= day_ago,
        )
    ) or 0
    if last_day >= settings.upload_rate_limit_per_day:
        raise UploadError(
            429,
            f"upload rate limit exceeded (per day: {settings.upload_rate_limit_per_day})",
        )


# ── Save Photo ──────────────────────────────────────────────────


async def save_visit_photo(
    db: AsyncSession,
    user: "AuthUser",
    content: bytes,
) -> VisitAttachmentOut:
    """
    保存照片到本地 volume + 写 visit_attachment 行。

    流程:
      1. 校验大小
      2. magic bytes 检测 mime,拒绝非 JPEG/PNG
      3. 限速检查(uploader_id 维度)
      4. 生成 UUID 文件名,写到 uploads/visits/{yyyymm}/{uuid}.{ext}
      5. INSERT visit_attachment(uploader_id, visit_record_id=NULL)
    """
    settings = get_settings()

    # 1. 大小
    if len(content) > settings.upload_max_size_bytes:
        raise UploadError(
            413,
            f"file too large (max {settings.upload_max_size_bytes // 1024 // 1024} MB)",
        )
    if len(content) < 100:
        raise UploadError(400, "file too small / empty")

    # 2. magic bytes
    mime = _detect_mime(content)
    if mime not in settings.upload_allowed_mimes:
        raise UploadError(
            415,
            f"unsupported mime type: {mime} (allowed: {settings.upload_allowed_mimes})",
        )
    ext = _MIME_TO_EXT[mime]

    uploader_id = UUID(user.id)

    # 3. 限速
    await _check_rate_limit(db, uploader_id)

    # 4. 落盘
    now = datetime.utcnow()
    yyyymm = now.strftime("%Y%m")
    file_id = uuid_lib.uuid4()
    rel_path = f"visits/{yyyymm}/{file_id}.{ext}"
    full_dir = Path(settings.upload_dir) / "visits" / yyyymm
    full_dir.mkdir(parents=True, exist_ok=True)
    full_path = Path(settings.upload_dir) / rel_path
    full_path.write_bytes(content)

    # 5. DB 行
    attachment = VisitAttachment(
        id=file_id,
        visit_record_id=None,  # 待 POST /visit-records 时绑定
        uploader_id=uploader_id,
        type=AttachmentType.PHOTO,
        storage_path=rel_path,
        file_size=len(content),
        mime_type=mime,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return VisitAttachmentOut(
        id=attachment.id,
        type=attachment.type,
        storage_path=attachment.storage_path,
        file_size=attachment.file_size,
        mime_type=attachment.mime_type,
        uploaded_at=attachment.uploaded_at,
    )


# ── Get Photo (proxy) ───────────────────────────────────────────


async def get_visit_photo_path(
    db: AsyncSession,
    user: "AuthUser",
    attachment_id: UUID,
) -> tuple[Path, str] | None:
    """
    返回 (local_path, mime_type) 或 None(无权 / 不存在)。

    §3.5.4 鉴权链路:
      attachment.uploader_id == current_user.id
        → owner 看自己的
      OR
      attachment.visit_record.salesperson_id 属于 current_user 的直属下属
        → manager 看下属
    """
    settings = get_settings()
    stmt = (
        select(
            VisitAttachment.storage_path,
            VisitAttachment.mime_type,
            VisitAttachment.uploader_id,
            VisitAttachment.visit_record_id,
            VisitRecord.salesperson_id,
        )
        .join(
            VisitRecord,
            VisitAttachment.visit_record_id == VisitRecord.id,
            isouter=True,  # orphan attachment 也能查
        )
        .where(VisitAttachment.id == attachment_id)
    )
    row = (await db.execute(stmt)).first()
    if row is None:
        return None

    storage_path, mime_type, uploader_id, _vid, sales_id = row
    current_id = UUID(user.id)

    # owner(上传者)
    if uploader_id == current_id:
        pass
    elif sales_id is not None:
        # 已绑 visit 的:check manager 链路
        manager_id = await db.scalar(
            select(User.manager_id).where(User.id == sales_id)
        )
        if manager_id is None or manager_id != current_id:
            return None
    else:
        # orphan,且 uploader 不是本人 → 拒
        return None

    full_path = Path(settings.upload_dir) / storage_path
    if not full_path.exists():
        return None
    return full_path, mime_type
