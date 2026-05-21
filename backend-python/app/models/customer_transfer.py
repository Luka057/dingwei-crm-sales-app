"""
CustomerTransfer 模型 — 客户转移请求(主管直接转 + 销售报批 双流程)。

引用:
- §3.4 客户归属(转移双流程)
- §3.5.6 cheatsheet:
    flow='manager_direct': pending → executed(立即,后端代码层一步)
    flow='sales_request':  pending → approved/rejected → executed
- §3.5.5 Q3 决议:1A 不允许 Sales 撤销已提交的 sales_request
- §3.5.4 边界 case #6:并发用乐观锁
    UPDATE customer SET owner_id=:new WHERE id=:cid AND owner_id=:old
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from app.db.base import Base, CreatedAt, FKUuid, OptFKUuid, PKUuid

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.user import User


class TransferFlow(str, enum.Enum):
    MANAGER_DIRECT = "manager_direct"
    SALES_REQUEST = "sales_request"


class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class CustomerTransfer(Base):
    __tablename__ = "customer_transfer"
    __table_args__ = (
        Index("IX_transfer_status", "status", "requested_at"),
        Index("IX_transfer_from_user", "from_user_id"),
        Index("IX_transfer_to_user", "to_user_id"),
        Index("IX_transfer_customer", "customer_id"),
        CheckConstraint(
            "flow IN ('manager_direct', 'sales_request')",
            name="CK_transfer_flow",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'executed')",
            name="CK_transfer_status",
        ),
    )

    id: Mapped[PKUuid]

    # ── 业务三人称 ─────────────────────────────────────────────
    customer_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("customer.id", ondelete="NO ACTION"),
        nullable=False,
    )
    from_user_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=False,
    )
    to_user_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=False,
    )
    # 发起人:sales_request → Sales 本人;manager_direct → Manager 本人
    initiated_by_user_id: Mapped[FKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=False,
    )

    # ── 流程 / 状态 ────────────────────────────────────────────
    flow: Mapped[TransferFlow] = mapped_column(
        Enum(
            TransferFlow,
            native_enum=False,
            length=32,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    status: Mapped[TransferStatus] = mapped_column(
        Enum(
            TransferStatus,
            native_enum=False,
            length=16,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=TransferStatus.PENDING,
    )

    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── 时间 ───────────────────────────────────────────────────
    requested_at: Mapped[CreatedAt]
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
    )
    reviewed_by_user_id: Mapped[OptFKUuid] = mapped_column(
        ForeignKey("user.id", ondelete="NO ACTION"),
        nullable=True,
    )

    # ── 关系 ───────────────────────────────────────────────────
    customer: Mapped[Customer] = relationship(
        "Customer",
        foreign_keys=[customer_id],
    )
    from_user: Mapped[User] = relationship("User", foreign_keys=[from_user_id])
    to_user: Mapped[User] = relationship("User", foreign_keys=[to_user_id])
    initiated_by_user: Mapped[User] = relationship(
        "User",
        foreign_keys=[initiated_by_user_id],
    )
    reviewed_by_user: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[reviewed_by_user_id],
    )

    def __repr__(self) -> str:
        return (
            f"<CustomerTransfer {self.customer_id} {self.from_user_id}→{self.to_user_id} "
            f"flow={self.flow.value} status={self.status.value}>"
        )
