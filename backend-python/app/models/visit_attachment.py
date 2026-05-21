"""
VisitAttachment 模型 — 拜访照片附件(Q7 决议:完整可用)。

引用:
- §3.5.5 Q7 决议:5MB / JPEG·PNG / magic bytes / per-user 限速 / owner+manager 鉴权
- §4.4 拜访照片上传(存储路径 uploads/visits/yyyymm/{uuid}.jpg)
- §3.5.4 边界 case #4:Manager 看下属照片鉴权链路:
    attachment → visit_record.salesperson_id → user.manager_id == current_user.id

1A 仅 type='photo';Phase 1B 加 audio/document 等。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, FKUuid, OptFKUuid, PKUuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.visit_record import VisitRecord


class AttachmentType(str, enum.Enum):
    PHOTO = "photo"
    # AUDIO = "audio"     # Phase 1B
    # DOCUMENT = "document"


class VisitAttachment(Base):
    __tablename__ = "visit_attachment"
    __table_args__ = (
        Index("IX_visit_attachment_visit", "visit_record_id"),
        Index("IX_visit_attachment_uploader_uploaded", "uploader_id", "uploaded_at"),
        CheckConstraint("type IN ('photo')", name="CK_attachment_type"),
    )

    id: Mapped[PKUuid]

    # Phase 1A 设计:visit_record_id 可空 — 允许"先上传后绑定 visit"
    # 流程:
    #   1. POST /uploads/visit-photo → 写 attachment(visit_record_id=NULL)
    #   2. POST /visit-records body 含 attachment_ids → UPDATE
    #      visit_attachment SET visit_record_id=:vid WHERE id IN (...)
    # Phase 1B 加 GC 任务清未绑定的 orphan attachment(超过 24h 等)。
    visit_record_id: Mapped[OptFKUuid] = mapped_column(
        ForeignKey("visit_record.id", ondelete="CASCADE"),
        nullable=True,
    )

    # uploader_id:谁上传的(权限 + 限速依据)。NOT NULL。
    # 即便 attachment 后来绑到别人的 visit_record(理论上不允许),
    # uploader_id 仍记录原始上传者。
    uploader_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=False,
    )

    type: Mapped[AttachmentType] = mapped_column(
        Enum(
            AttachmentType,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=AttachmentType.PHOTO,
    )

    # 存储路径(相对 settings.upload_dir),如 visits/202605/{uuid}.jpg
    storage_path: Mapped[str] = mapped_column(Unicode(255), nullable=False)

    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    mime_type: Mapped[str] = mapped_column(Unicode(32), nullable=False)

    # 上传时由 upload_service 经 magic bytes 校验后填入
    uploaded_at: Mapped[CreatedAt]

    # ── 关系 ───────────────────────────────────────────────────
    visit_record: Mapped["VisitRecord | None"] = relationship(
        "VisitRecord",
        back_populates="attachments",
        foreign_keys=[visit_record_id],
    )
    uploader: Mapped["User"] = relationship(
        "User",
        foreign_keys=[uploader_id],
    )

    def __repr__(self) -> str:
        return f"<VisitAttachment {self.storage_path} ({self.file_size} bytes)>"
