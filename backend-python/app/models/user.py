"""
User 模型 — 销售员 / 主管。

引用:`docs/需求文档-v2.md §3.1-3.2 角色定义` + §5.3 共享 ID 预留字段。

角色枚举:只 sales + manager,**不存在 boss**(老板用老板端)。
但 seed 时会建一个 boss 账号供 Phase 2 回传测试,该账号在本应用永不登录。
为了 seed 时不破坏 enum,我们仍把 'boss' 留在枚举里,但业务层从不允许其登录本应用。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import (
    Base,
    CreatedAt,
    ExternalId,
    OptFKUuid,
    PKUuid,
    SourceSystem,
    SyncedAt,
    UpdatedAt,
)

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.plan import Plan
    from app.models.visit_record import VisitRecord
    from app.models.weekly_report import WeeklyReport


class UserRole(str, enum.Enum):
    """业务人员端只识别 sales + manager。boss 仅 seed 留位。"""

    SALES = "sales"
    MANAGER = "manager"
    BOSS = "boss"  # seed 留位,本应用不允许登录(auth service 校验)


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    RESIGNED = "resigned"


class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        # 索引(命名遵守 SQL Server 习惯 IX_<table>_<cols>)
        Index(
            "IX_user_external",
            "external_id",
            mssql_where="external_id IS NOT NULL",  # SQL Server 过滤索引
        ),
        Index("IX_user_manager", "manager_id"),
        # 软枚举 CHECK(native_enum=False 模式)
        CheckConstraint(
            "role IN ('sales', 'manager', 'boss')",
            name="CK_user_role",
        ),
        CheckConstraint(
            "status IN ('active', 'disabled', 'resigned')",
            name="CK_user_status",
        ),
    )

    # ── PK ──────────────────────────────────────────────────────
    id: Mapped[PKUuid]

    # ── 业务字段 ────────────────────────────────────────────────
    username: Mapped[str] = mapped_column(Unicode(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Unicode(255), nullable=False)
    name: Mapped[str] = mapped_column(Unicode(64), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=UserStatus.ACTIVE,
    )

    # ── 主管关联(self-FK,RESTRICT 默认) ──────────────────────
    manager_id: Mapped[OptFKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=True,
    )

    # ── 集成预留(§5.3 共享 ID) ────────────────────────────────
    external_id: Mapped[ExternalId]
    source_system: Mapped[SourceSystem]
    synced_at: Mapped[SyncedAt]

    # ── 时间戳 ──────────────────────────────────────────────────
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    # ── 关系 ────────────────────────────────────────────────────
    manager: Mapped[User | None] = relationship(
        "User",
        remote_side="User.id",
        back_populates="subordinates",
    )
    subordinates: Mapped[list[User]] = relationship(
        "User",
        back_populates="manager",
    )
    owned_customers: Mapped[list[Customer]] = relationship(
        "Customer",
        back_populates="owner",
        foreign_keys="Customer.owner_id",
    )
    plans: Mapped[list[Plan]] = relationship(
        "Plan",
        back_populates="salesperson",
        foreign_keys="Plan.salesperson_id",
    )
    visit_records: Mapped[list[VisitRecord]] = relationship(
        "VisitRecord",
        back_populates="salesperson",
        foreign_keys="VisitRecord.salesperson_id",
    )
    weekly_reports: Mapped[list[WeeklyReport]] = relationship(
        "WeeklyReport",
        back_populates="salesperson",
        foreign_keys="WeeklyReport.salesperson_id",
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"
