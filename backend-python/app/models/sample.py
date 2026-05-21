"""
Sample 模型 — 样板(1A 仅建表,无 router)。

引用:
- §3.5.2 端点矩阵:Samples 相关延后(模型已建,字段为 Phase 2 向量库集成预留)
- §5.3 共享 ID(external_id 对接老板端样板号)
- §6.4 AI 找板(Phase 2 实施,1A stub)

字段对齐 docs/数据字典.md samples 表。
状态用拼音键(qiyang/zhongban/queren/yizhuandingdan/yifangqi),DTO 层映射中文显示。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    from app.models.customer import Customer


class SampleStatus(str, enum.Enum):
    """状态拼音键 — 显示中文在 DTO 层映射。"""

    QIYANG = "qiyang"           # 起样
    ZHONGBAN = "zhongban"       # 中板
    QUEREN = "queren"           # 确认
    YIZHUANDINGDAN = "yizhuandingdan"  # 已转订单
    YIFANGQI = "yifangqi"       # 已放弃


class Sample(Base):
    __tablename__ = "sample"
    __table_args__ = (
        Index("IX_sample_customer", "customer_id"),
        Index(
            "IX_sample_external",
            "external_id",
            mssql_where="external_id IS NOT NULL",
        ),
        CheckConstraint(
            "status IN ('qiyang', 'zhongban', 'queren', 'yizhuandingdan', 'yifangqi')",
            name="CK_sample_status",
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

    sample_no: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[SampleStatus] = mapped_column(
        Enum(
            SampleStatus,
            native_enum=False,
            length=32,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=SampleStatus.QIYANG,
    )

    # 工艺参数(AI 找板 metadata filter 用)
    width: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tension: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ribbon_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)

    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── 集成预留 ───────────────────────────────────────────────
    external_id: Mapped[ExternalId]
    source_system: Mapped[SourceSystem]
    synced_at: Mapped[SyncedAt]

    # ── 时间戳 ─────────────────────────────────────────────────
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    # ── 关系 ───────────────────────────────────────────────────
    customer: Mapped[Customer] = relationship(
        "Customer",
        back_populates="samples",
        foreign_keys=[customer_id],
    )

    def __repr__(self) -> str:
        return f"<Sample {self.sample_no} ({self.status.value})>"
