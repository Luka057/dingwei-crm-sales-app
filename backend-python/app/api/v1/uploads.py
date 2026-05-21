"""
Uploads router(Q7 决议:照片上传完整可用)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /uploads/visit-photo       Sales/Manager 上传(per-user 限速)
- GET /uploads/visit-photo/{id}   Sales(owner) / Manager(owner 或下属上传)

§3.5.4 边界 case #4:Manager 看下属照片鉴权链路:
  attachment → visit_record.salesperson_id → user.manager_id == current_user.id

Q7 实施细节(§11.1):
- 5MB / JPEG·PNG
- magic bytes 校验(python-magic),不信任前端扩展名
- per-user 限速(默认 30/小时 + 100/天,O3 待最终敲定)
- 本地 docker volume,路径 uploads/visits/yyyymm/{uuid}.jpg
- 唯一文件名 UUID,防穷举
"""

from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, DBSession
from app.schemas.visit_record import VisitAttachmentOut

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "/visit-photo",
    response_model=VisitAttachmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="上传拜访照片",
)
async def upload_visit_photo(
    user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),  # noqa: B008
) -> VisitAttachmentOut:
    """流程:
    1. 校验大小 (settings.upload_max_size_bytes)
    2. magic bytes 校验 mime(python-magic),拒绝非 JPEG/PNG
    3. per-user 限速(查 visit_attachment 近 1 小时/1 天的上传量)
    4. 生成 UUID 文件名,落到 uploads/visits/{yyyymm}/{uuid}.jpg
    5. INSERT visit_attachment(visit_record_id=NULL,稍后绑定)
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.5 — uploads module)",
    )


@router.get(
    "/visit-photo/{attachment_id}",
    response_class=FileResponse,
    summary="查看拜访照片(JWT + owner/manager 鉴权)",
)
async def get_visit_photo(
    attachment_id: UUID,
    user: CurrentUser,
    db: DBSession,
) -> FileResponse:
    """鉴权链路(§3.5.4 边界 case #4):
    SELECT a.storage_path FROM visit_attachment a
    JOIN visit_record v ON a.visit_record_id = v.id
    JOIN [user] u ON v.salesperson_id = u.id
    WHERE a.id = :aid AND (
      v.salesperson_id = :current_uid    -- owner 看自己的
      OR u.manager_id = :current_uid     -- manager 看下属的
    )
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.5 — uploads module)",
    )
