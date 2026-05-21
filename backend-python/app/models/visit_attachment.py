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

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, FKUuid, PKUuid

if TYPE_CHECKING:
    from app.models.visit_record import VisitRecord


class AttachmentType(str, enum.Enum):
    PHOTO = "photo"
    # AUDIO = "audio"     # Phase 1B
    # DOCUMENT = "document"


class VisitAttachment(Base):
    __tablename__ = "visit_attachment"
    __table_args__ = (
        Index("IX_visit_attachment_visit", "visit_record_id"),
        CheckConstraint("type IN ('photo')", name="CK_attachment_type"),
    )

    id: Mapped[PKUuid]

    visit_record_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("visit_record.id", ondelete="CASCADE"),
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
    storage_path: Mapped[str] = mapped_column(String(255), nullable=False)

    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    mime_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # 上传时由 upload_service 经 magic bytes 校验后填入
    uploaded_at: Mapped[CreatedAt]

    # ── 关系 ───────────────────────────────────────────────────
    visit_record: Mapped[VisitRecord] = relationship(
        "VisitRecord",
        back_populates="attachments",
        foreign_keys=[visit_record_id],
    )

    def __repr__(self) -> str:
        return f"<VisitAttachment {self.storage_path} ({self.file_size} bytes)>"
