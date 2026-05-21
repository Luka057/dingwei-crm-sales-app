"""
VisitRecord 模型 — 拜访记录。

引用:
- §4.1 销售的一天(现场实时录入,文字 + 照片)
- §4.4 拜访照片上传(关联 VisitAttachment)
- §3.5.4 边界 case #2:客户转移后 salesperson_id 不变(历史归原销售)
- §3.5.4 边界 case #4:Manager 看下属照片鉴权链路

字段对齐 docs/数据字典.md visit_records 表。
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from app.db.base import Base, CreatedAt, FKUuid, PKUuid

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.user import User
    from app.models.visit_attachment import VisitAttachment


class VisitMethod(str, enum.Enum):
    OFFLINE = "offline"
    PHONE = "phone"
    WECHAT = "wechat"


class VisitIntention(str, enum.Enum):
    GOOD = "good"
    LIKELY_ORDER = "likely_order"
    WAIT = "wait"
    NONE = "none"


class VisitRecord(Base):
    __tablename__ = "visit_record"
    __table_args__ = (
        Index("IX_visit_owner_visitat", "salesperson_id", "visit_at"),
        Index("IX_visit_customer_visitat", "customer_id", "visit_at"),
        CheckConstraint(
            "method IN ('offline', 'phone', 'wechat')",
            name="CK_visit_method",
        ),
        CheckConstraint(
            "intention IN ('good', 'likely_order', 'wait', 'none')",
            name="CK_visit_intention",
        ),
    )

    id: Mapped[PKUuid]

    customer_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("customer.id", ondelete="NO ACTION"),
        nullable=False,
    )
    salesperson_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=False,
    )

    visit_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
    )
    method: Mapped[VisitMethod] = mapped_column(
        Enum(
            VisitMethod,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    intention: Mapped[VisitIntention] = mapped_column(
        Enum(
            VisitIntention,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=VisitIntention.NONE,
    )

    target_person: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI 摘要(1A stub 写固定文案;Phase 1B DeepSeek 真接入)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    next_follow_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
    )

    created_at: Mapped[CreatedAt]

    # ── 关系 ───────────────────────────────────────────────────
    customer: Mapped[Customer] = relationship(
        "Customer",
        back_populates="visit_records",
        foreign_keys=[customer_id],
    )
    salesperson: Mapped[User] = relationship(
        "User",
        back_populates="visit_records",
        foreign_keys=[salesperson_id],
    )
    attachments: Mapped[list[VisitAttachment]] = relationship(
        "VisitAttachment",
        back_populates="visit_record",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<VisitRecord {self.customer_id} @ {self.visit_at}>"
