"""
Plan 模型 — 销售日历日程项。

引用:
- §5.4 个人 vs 业务计划(is_personal 字段)
- §3.5.5 Q8 决议:后端推断 + 前端 toggle 可改
- §3.5.4 边界 case #3:type='custom' AND customer_id IS NULL 默认 is_personal=True

关键约束:
- 状态机:pending → done / cancelled,无审批(§3.5.6 cheatsheet)
- 主管看下属时自动过滤 is_personal=True(§3.5.3 数据可见性硬规则)
- 外键 customer_id 用 ON DELETE SET NULL(方案 1A.2 唯一一处 SetNull)
- 索引 IX_plan_owner_personal 用于"主管视图过滤 is_personal=0"
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Index, Unicode, UnicodeText
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from app.db.base import Base, CreatedAt, FKUuid, OptFKUuid, PKUuid, UpdatedAt

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.user import User


class PlanType(str, enum.Enum):
    VISIT = "visit"
    CUSTOM = "custom"


class PlanStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


class Plan(Base):
    __tablename__ = "plan"
    __table_args__ = (
        Index("IX_plan_owner_scheduled", "salesperson_id", "scheduled_at"),  # 日历热点
        Index("IX_plan_owner_personal", "salesperson_id", "is_personal"),    # 主管过滤
        CheckConstraint("type IN ('visit', 'custom')", name="CK_plan_type"),
        CheckConstraint(
            "status IN ('pending', 'done', 'cancelled')",
            name="CK_plan_status",
        ),
    )

    id: Mapped[PKUuid]

    salesperson_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=False,
    )

    # customer_id 可空(custom plan 无客户);SetNull 在客户删除时保留 plan 行为孤儿
    # 注:1A 不删客户(customer.status=inactive 即可),此处保险设计
    customer_id: Mapped[OptFKUuid] = mapped_column(
        ForeignKey("customer.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(Unicode(128), nullable=False)
    type: Mapped[PlanType] = mapped_column(
        Enum(
            PlanType,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    status: Mapped[PlanStatus] = mapped_column(
        Enum(
            PlanStatus,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=PlanStatus.PENDING,
    )

    # ── Q8 决议:is_personal 后端推断 + 前端 toggle 可改 ─────────
    is_personal: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",  # SQL Server BIT 默认 0
    )

    # ── 时间戳 ─────────────────────────────────────────────────
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    # ── 关系 ───────────────────────────────────────────────────
    salesperson: Mapped[User] = relationship(
        "User",
        back_populates="plans",
        foreign_keys=[salesperson_id],
    )
    customer: Mapped[Customer | None] = relationship(
        "Customer",
        back_populates="plans",
        foreign_keys=[customer_id],
    )

    def __repr__(self) -> str:
        personal = " [personal]" if self.is_personal else ""
        return f"<Plan {self.title} @ {self.scheduled_at}{personal}>"
