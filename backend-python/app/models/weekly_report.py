"""
WeeklyReport 模型 — 周报(销售自评 + 主管退回闭环)。

引用:
- §4.2 销售的一周(覆盖当周非上周,4 段固定结构)
- §3.5.6 状态机:draft → submitted → reopened → submitted(submit 无审批)
- §5.5 周报字段与 plan 表关系(next_plan 与 plan 表不同步)
- §0 术语对照:submit ≠ approve;reopen ≠ reject

约束:
- UQ_weekly_owner_week:一个销售一周一份
- 主管看下属仅 status IN ('submitted', 'reopened'),draft 看不见(§3.5.3)
"""

from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    UnicodeText,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, FKUuid, PKUuid, UpdatedAt

if TYPE_CHECKING:
    from app.models.user import User


class WeeklyReportStatus(str, enum.Enum):
    """状态机见 §3.5.6 / §4.5。"""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    REOPENED = "reopened"


class WeeklyReport(Base):
    __tablename__ = "weekly_report"
    __table_args__ = (
        UniqueConstraint(
            "salesperson_id",
            "week_start",
            name="UQ_weekly_owner_week",
        ),
        Index("IX_weekly_owner_status", "salesperson_id", "status"),
        CheckConstraint(
            "status IN ('draft', 'submitted', 'reopened')",
            name="CK_weekly_status",
        ),
    )

    id: Mapped[PKUuid]

    salesperson_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=False,
    )

    # 周一日期(写入时算 ISO 周一)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)

    # ── 4 段固定结构(§4.2 / §3.5.6) ─────────────────────────
    # ① summary 本周工作总结(必填,前端校验)
    summary: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    # ② next_plan 下周工作计划 — 自由文本,与 plan 表不同步(§5.5)
    next_plan: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    # ③ notes 备注事项
    notes: Mapped[str | None] = mapped_column(UnicodeText, nullable=True)
    # ④ attachments 附件(1A 字段保留不开 UI;Phase 1B 实现)
    attachments: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # ── 状态 ───────────────────────────────────────────────────
    status: Mapped[WeeklyReportStatus] = mapped_column(
        Enum(
            WeeklyReportStatus,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=WeeklyReportStatus.DRAFT,
    )

    # ── 时间戳 ─────────────────────────────────────────────────
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    # ── 关系 ───────────────────────────────────────────────────
    salesperson: Mapped[User] = relationship(
        "User",
        back_populates="weekly_reports",
        foreign_keys=[salesperson_id],
    )

    def __repr__(self) -> str:
        return (
            f"<WeeklyReport {self.salesperson_id} week_start={self.week_start} "
            f"status={self.status.value}>"
        )
