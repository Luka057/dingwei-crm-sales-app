"""
Customer 模型 — 客户主数据。

引用:
- §3.4 客户归属(单 owner_id)
- §5.1 A/B/C 分级(1A 默认 B + ai_score 留位 Phase 2)
- §5.2 超期判定(运行时计算,不存表)
- §5.3 共享 ID(external_id / source_system / synced_at)
"""

from __future__ import annotations

import enum
from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from app.db.base import (
    Base,
    CreatedAt,
    ExternalId,
    FKUuid,
    PKUuid,
    SourceSystem,
    SyncedAt,
    UpdatedAt,
)

if TYPE_CHECKING:
    from app.models.plan import Plan
    from app.models.sample import Sample
    from app.models.user import User
    from app.models.visit_record import VisitRecord


class CustomerLevel(str, enum.Enum):
    """A 14d / B 30d / C 60d 超期阈值,详见 §5.2。"""

    A = "A"
    B = "B"
    C = "C"


class CustomerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Customer(Base):
    __tablename__ = "customer"
    __table_args__ = (
        Index("IX_customer_owner", "owner_id"),
        Index("IX_customer_owner_level", "owner_id", "level"),
        Index("IX_customer_owner_lastvisit", "owner_id", "last_visit_at"),  # 超期热点
        Index(
            "IX_customer_external",
            "external_id",
            mssql_where="external_id IS NOT NULL",
        ),
        CheckConstraint("level IN ('A', 'B', 'C')", name="CK_customer_level"),
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="CK_customer_status",
        ),
    )

    # ── PK ──────────────────────────────────────────────────────
    id: Mapped[PKUuid]

    # ── 基本资料 ───────────────────────────────────────────────
    name: Mapped[str] = mapped_column(Unicode(128), nullable=False)
    short_name: Mapped[str | None] = mapped_column(Unicode(64), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(Unicode(64), nullable=True)
    contact_title: Mapped[str | None] = mapped_column(Unicode(64), nullable=True)
    phone: Mapped[str | None] = mapped_column(Unicode(32), nullable=True)
    address: Mapped[str | None] = mapped_column(Unicode(255), nullable=True)

    # ── 等级 / 状态 ────────────────────────────────────────────
    level: Mapped[CustomerLevel] = mapped_column(
        Enum(
            CustomerLevel,
            native_enum=False,
            length=4,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=CustomerLevel.B,  # 1A 默认 B
    )
    # Phase 2 AI 估评写入(0-100),1A 留位
    ai_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(
            CustomerStatus,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=CustomerStatus.ACTIVE,
    )

    # ── 归属(§3.4 单 owner) ──────────────────────────────────
    owner_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=False,
    )

    # ── 拜访时间(超期判定基准) ──────────────────────────────
    last_visit_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
    )

    # ── 集成预留 ───────────────────────────────────────────────
    external_id: Mapped[ExternalId]
    source_system: Mapped[SourceSystem]
    synced_at: Mapped[SyncedAt]

    # ── 时间戳 ─────────────────────────────────────────────────
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    # ── 关系 ───────────────────────────────────────────────────
    owner: Mapped[User] = relationship(
        "User",
        back_populates="owned_customers",
        foreign_keys=[owner_id],
    )
    plans: Mapped[list[Plan]] = relationship(
        "Plan",
        back_populates="customer",
        foreign_keys="Plan.customer_id",
    )
    visit_records: Mapped[list[VisitRecord]] = relationship(
        "VisitRecord",
        back_populates="customer",
        foreign_keys="VisitRecord.customer_id",
    )
    samples: Mapped[list[Sample]] = relationship(
        "Sample",
        back_populates="customer",
        foreign_keys="Sample.customer_id",
    )

    def __repr__(self) -> str:
        return f"<Customer {self.name} ({self.level.value})>"
