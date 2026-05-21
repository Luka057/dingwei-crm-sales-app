"""
Customer Transfer service.

双 flow + 4 状态(§3.4 / §3.5.6):
  manager_direct: Manager 发起,后端代码一步 → executed
  sales_request:  Sales 发起,pending → approved/rejected → executed
                  (Q3:1A 不允许 Sales 撤销)

§3.5.4 边界 case #6 客户转移并发:
  乐观锁:UPDATE customer SET owner_id=:new
         WHERE id=:cid AND owner_id=:expected_old
  影响 0 行 → 409 conflict(并发被插队)

权限校验(§3.5.2):
- POST manager_direct:role=manager + customer.owner_id 是 manager 直属下属
- POST sales_request: role=sales + customer.owner_id == current
- approve/reject: manager-only + 必须是 manager 直属下属发起的 pending
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.customer_transfer import (
    CustomerTransfer,
    TransferFlow,
    TransferStatus,
)
from app.models.user import User, UserRole
from app.schemas.transfer import CustomerTransferCreate, CustomerTransferOut

if TYPE_CHECKING:
    from app.core.deps import AuthUser


class TransferError(Exception):
    def __init__(self, code: int, msg: str) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg


async def _to_out(db: AsyncSession, t: CustomerTransfer) -> CustomerTransferOut:
    """ORM → DTO,带 join 出来的名字。"""
    # 一次性查所有相关名字
    ids = {t.customer_id, t.from_user_id, t.to_user_id}
    customer_name = await db.scalar(
        select(Customer.name).where(Customer.id == t.customer_id)
    )
    user_names: dict[UUID, str] = {}
    for uid, name in (
        await db.execute(
            select(User.id, User.name).where(User.id.in_({t.from_user_id, t.to_user_id}))
        )
    ).all():
        user_names[uid] = name

    return CustomerTransferOut(
        id=t.id,
        customer_id=t.customer_id,
        customer_name=customer_name,
        from_user_id=t.from_user_id,
        from_user_name=user_names.get(t.from_user_id),
        to_user_id=t.to_user_id,
        to_user_name=user_names.get(t.to_user_id),
        initiated_by_user_id=t.initiated_by_user_id,
        flow=t.flow,
        status=t.status,
        reason=t.reason,
        requested_at=t.requested_at,
        reviewed_at=t.reviewed_at,
        reviewed_by_user_id=t.reviewed_by_user_id,
    )


# ── Create ──────────────────────────────────────────────────────


async def create_transfer(
    db: AsyncSession,
    user: "AuthUser",
    payload: CustomerTransferCreate,
) -> CustomerTransferOut:
    current_id = UUID(user.id)

    # 拉 customer
    customer = (
        await db.execute(select(Customer).where(Customer.id == payload.customer_id))
    ).scalar_one_or_none()
    if customer is None:
        raise TransferError(404, "customer not found")

    # 拉 to_user
    to_user = (
        await db.execute(select(User).where(User.id == payload.to_user_id))
    ).scalar_one_or_none()
    if to_user is None:
        raise TransferError(404, "target user not found")
    if to_user.role not in (UserRole.SALES, UserRole.MANAGER):
        raise TransferError(400, "target user must be sales or manager")
    if to_user.id == customer.owner_id:
        raise TransferError(400, "target user is already the owner")

    # 校验 flow 合法性
    if payload.flow == TransferFlow.SALES_REQUEST:
        if not user.is_sales:
            raise TransferError(
                403, "sales_request requires sales role (managers use manager_direct)"
            )
        if customer.owner_id != current_id:
            raise TransferError(403, "you don't own this customer")
        # 1A 草案(O5):只能转给同 manager_id 的同事
        current_user_row = (
            await db.execute(select(User).where(User.id == current_id))
        ).scalar_one()
        if (
            to_user.manager_id != current_user_row.manager_id
            or to_user.manager_id is None
        ):
            raise TransferError(
                400,
                "1A: can only transfer to colleagues under the same manager",
            )
        # 创建 pending 请求,不动 customer.owner_id
        from_user_id = customer.owner_id
        transfer = CustomerTransfer(
            customer_id=customer.id,
            from_user_id=from_user_id,
            to_user_id=to_user.id,
            initiated_by_user_id=current_id,
            flow=TransferFlow.SALES_REQUEST,
            status=TransferStatus.PENDING,
            reason=payload.reason,
        )
        db.add(transfer)
        await db.commit()
        await db.refresh(transfer)
        return await _to_out(db, transfer)

    # manager_direct
    if not user.is_manager:
        raise TransferError(
            403, "manager_direct requires manager role (sales use sales_request)"
        )

    # 校验 customer 当前 owner 是 manager 直属下属
    current_owner_manager_id = await db.scalar(
        select(User.manager_id).where(User.id == customer.owner_id)
    )
    if current_owner_manager_id != current_id:
        raise TransferError(403, "customer owner is not your subordinate")

    # 校验 to_user 也是 manager 直属下属(或 manager 自己)
    if to_user.id != current_id and to_user.manager_id != current_id:
        raise TransferError(
            403, "target user is not your subordinate (or yourself)"
        )

    # 乐观锁更新 customer.owner_id
    from_user_id = customer.owner_id
    result = await db.execute(
        update(Customer)
        .where(
            Customer.id == customer.id,
            Customer.owner_id == from_user_id,
        )
        .values(owner_id=to_user.id)
    )
    if result.rowcount == 0:
        raise TransferError(409, "concurrent update detected, please retry")

    # 写 transfer 记录(executed)
    transfer = CustomerTransfer(
        customer_id=customer.id,
        from_user_id=from_user_id,
        to_user_id=to_user.id,
        initiated_by_user_id=current_id,
        flow=TransferFlow.MANAGER_DIRECT,
        status=TransferStatus.EXECUTED,
        reason=payload.reason,
        reviewed_at=datetime.utcnow(),
        reviewed_by_user_id=current_id,
    )
    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)
    return await _to_out(db, transfer)


# ── List ────────────────────────────────────────────────────────


async def list_transfers(
    db: AsyncSession,
    user: "AuthUser",
    status_filter: str | None = None,
) -> list[CustomerTransferOut]:
    """
    Sales:看自己 initiated 的全部
    Manager:看自己 initiated 的 + 下属发起的 pending(待审)
    """
    current_id = UUID(user.id)

    if user.is_sales:
        stmt = select(CustomerTransfer).where(
            CustomerTransfer.initiated_by_user_id == current_id
        )
    else:
        # manager:union 两部分
        # 1) 自己 initiated
        # 2) 下属 sales_request 的 pending
        sub_ids = [
            row[0]
            for row in (
                await db.execute(select(User.id).where(User.manager_id == current_id))
            ).all()
        ]
        stmt = select(CustomerTransfer).where(
            or_(
                CustomerTransfer.initiated_by_user_id == current_id,
                and_(
                    CustomerTransfer.flow == TransferFlow.SALES_REQUEST,
                    CustomerTransfer.from_user_id.in_(sub_ids) if sub_ids else False,
                ),
            )
        )

    if status_filter:
        stmt = stmt.where(CustomerTransfer.status == status_filter)

    stmt = stmt.order_by(CustomerTransfer.requested_at.desc())
    transfers = (await db.execute(stmt)).scalars().all()
    return [await _to_out(db, t) for t in transfers]


# ── Approve(manager-only) ────────────────────────────────────


async def approve_transfer(
    db: AsyncSession,
    manager: "AuthUser",
    transfer_id: UUID,
) -> CustomerTransferOut | None:
    """事务:乐观锁 UPDATE customer.owner_id + 标 executed。"""
    current_id = UUID(manager.id)

    transfer = (
        await db.execute(
            select(CustomerTransfer).where(CustomerTransfer.id == transfer_id)
        )
    ).scalar_one_or_none()
    if transfer is None:
        return None
    if transfer.flow != TransferFlow.SALES_REQUEST:
        raise TransferError(
            400, f"can only approve sales_request flow (got {transfer.flow.value})"
        )
    if transfer.status != TransferStatus.PENDING:
        raise TransferError(
            409, f"transfer status is {transfer.status.value}, expected pending"
        )

    # 校验 from_user 是 manager 直属下属
    from_user_manager_id = await db.scalar(
        select(User.manager_id).where(User.id == transfer.from_user_id)
    )
    if from_user_manager_id != current_id:
        return None  # 不是自己下属发起的,不可审

    # 乐观锁更新 customer.owner_id
    result = await db.execute(
        update(Customer)
        .where(
            Customer.id == transfer.customer_id,
            Customer.owner_id == transfer.from_user_id,
        )
        .values(owner_id=transfer.to_user_id)
    )
    if result.rowcount == 0:
        raise TransferError(
            409,
            "customer owner has changed concurrently, please review and retry",
        )

    transfer.status = TransferStatus.EXECUTED
    transfer.reviewed_at = datetime.utcnow()
    transfer.reviewed_by_user_id = current_id
    await db.commit()
    await db.refresh(transfer)
    return await _to_out(db, transfer)


# ── Reject(manager-only) ─────────────────────────────────────


async def reject_transfer(
    db: AsyncSession,
    manager: "AuthUser",
    transfer_id: UUID,
) -> CustomerTransferOut | None:
    current_id = UUID(manager.id)
    transfer = (
        await db.execute(
            select(CustomerTransfer).where(CustomerTransfer.id == transfer_id)
        )
    ).scalar_one_or_none()
    if transfer is None:
        return None
    if transfer.flow != TransferFlow.SALES_REQUEST:
        raise TransferError(400, "can only reject sales_request flow")
    if transfer.status != TransferStatus.PENDING:
        raise TransferError(409, f"transfer status is {transfer.status.value}")

    from_user_manager_id = await db.scalar(
        select(User.manager_id).where(User.id == transfer.from_user_id)
    )
    if from_user_manager_id != current_id:
        return None

    transfer.status = TransferStatus.REJECTED
    transfer.reviewed_at = datetime.utcnow()
    transfer.reviewed_by_user_id = current_id
    await db.commit()
    await db.refresh(transfer)
    return await _to_out(db, transfer)
