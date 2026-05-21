"""
Plan service.

引用:
- §3.5.5 Q8:is_personal 后端推断 + 前端 toggle 可改
  - type='custom' AND customer_id IS NULL 创建时默认 True
  - 其他默认 False
  - 销售可显式 override(payload.is_personal 不为 None 时按显式值)
- §3.5.3 SELECT 必带 WHERE salesperson_id = current_user.id
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.plan import Plan, PlanStatus, PlanType
from app.schemas.plan import (
    CalendarDay,
    CalendarResponse,
    PlanCreate,
    PlanItem,
    PlanUpdate,
)

if TYPE_CHECKING:
    from app.core.deps import AuthUser


def _infer_is_personal(plan_type: PlanType, customer_id: UUID | None) -> bool:
    """Q8 后端推断:type=custom AND customer_id IS NULL → 个人提醒。"""
    return plan_type == PlanType.CUSTOM and customer_id is None


async def _to_item(db: AsyncSession, p: Plan) -> PlanItem:
    """ORM → DTO(join 客户名)。"""
    customer_name: str | None = None
    if p.customer_id:
        customer_name = await db.scalar(
            select(Customer.name).where(Customer.id == p.customer_id)
        )
    return PlanItem(
        id=p.id,
        type=p.type,
        customer_id=p.customer_id,
        customer_name=customer_name,
        title=p.title,
        scheduled_at=p.scheduled_at,
        status=p.status,
        is_personal=p.is_personal,
        content=p.content,
    )


# ── Calendar ────────────────────────────────────────────────────


async def get_calendar(
    db: AsyncSession,
    user: "AuthUser",
    year: int,
    month: int,
) -> CalendarResponse:
    """按月返回 plan 列表,按日分组(Sales/Manager 看本人 plan 全部含 is_personal)。"""
    _, days_in_month = monthrange(year, month)
    start = datetime(year, month, 1, 0, 0, 0)
    end = datetime(year, month, days_in_month, 23, 59, 59, 999999)

    stmt = (
        select(Plan)
        .where(
            Plan.salesperson_id == UUID(user.id),
            Plan.scheduled_at >= start,
            Plan.scheduled_at <= end,
        )
        .order_by(Plan.scheduled_at)
    )
    plans = (await db.execute(stmt)).scalars().all()

    # 收集所有 customer_id 一次性 join,避免 N+1
    customer_names: dict[UUID, str] = {}
    cust_ids = {p.customer_id for p in plans if p.customer_id}
    if cust_ids:
        name_stmt = select(Customer.id, Customer.name).where(Customer.id.in_(cust_ids))
        for cid, cname in (await db.execute(name_stmt)).all():
            customer_names[cid] = cname

    # 按日期分组
    by_day: dict[date, list[PlanItem]] = {}
    for p in plans:
        d = p.scheduled_at.date()
        by_day.setdefault(d, []).append(
            PlanItem(
                id=p.id,
                type=p.type,
                customer_id=p.customer_id,
                customer_name=customer_names.get(p.customer_id) if p.customer_id else None,
                title=p.title,
                scheduled_at=p.scheduled_at,
                status=p.status,
                is_personal=p.is_personal,
                content=p.content,
            )
        )

    days = [
        CalendarDay(date=d, items=by_day[d])
        for d in sorted(by_day.keys())
    ]
    return CalendarResponse(year=year, month=month, days=days)


# ── Create ──────────────────────────────────────────────────────


async def create_plan(
    db: AsyncSession,
    user: "AuthUser",
    payload: PlanCreate,
) -> PlanItem:
    """Q8 决议:is_personal 推断 + override。

    校验:visit 类型必须带 customer;customer 必须属于本人。
    """
    if payload.type == PlanType.VISIT and payload.customer_id is None:
        raise ValueError("visit type plan must include customer_id")

    if payload.customer_id:
        customer_owner = await db.scalar(
            select(Customer.owner_id).where(Customer.id == payload.customer_id)
        )
        if customer_owner is None:
            raise ValueError("customer not found")
        if customer_owner != UUID(user.id):
            raise PermissionError("customer not owned by current user")

    # is_personal:None → 后端推断;否则用前端显式值
    is_personal = (
        _infer_is_personal(payload.type, payload.customer_id)
        if payload.is_personal is None
        else payload.is_personal
    )

    plan = Plan(
        salesperson_id=UUID(user.id),
        customer_id=payload.customer_id,
        title=payload.title,
        type=payload.type,
        scheduled_at=payload.scheduled_at,
        content=payload.content,
        status=PlanStatus.PENDING,
        is_personal=is_personal,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return await _to_item(db, plan)


# ── Update ──────────────────────────────────────────────────────


async def update_plan(
    db: AsyncSession,
    user: "AuthUser",
    plan_id: UUID,
    payload: PlanUpdate,
) -> PlanItem | None:
    """部分更新。owner 校验 — 不是本人的返 None(调用方 404)。"""
    plan = (
        await db.execute(
            select(Plan).where(
                Plan.id == plan_id,
                Plan.salesperson_id == UUID(user.id),
            )
        )
    ).scalar_one_or_none()
    if plan is None:
        return None

    data = payload.model_dump(exclude_unset=True)

    # customer 切换时需重新验证 owner
    if "customer_id" in data and data["customer_id"]:
        customer_owner = await db.scalar(
            select(Customer.owner_id).where(Customer.id == data["customer_id"])
        )
        if customer_owner is None or customer_owner != UUID(user.id):
            raise PermissionError("customer not owned by current user")

    for key, value in data.items():
        setattr(plan, key, value)

    await db.commit()
    await db.refresh(plan)
    return await _to_item(db, plan)


# ── Delete ──────────────────────────────────────────────────────


async def delete_plan(
    db: AsyncSession,
    user: "AuthUser",
    plan_id: UUID,
) -> bool:
    """返回 True 表示删除成功,False 表示找不到或没权限(调用方 404)。"""
    plan = (
        await db.execute(
            select(Plan).where(
                Plan.id == plan_id,
                Plan.salesperson_id == UUID(user.id),
            )
        )
    ).scalar_one_or_none()
    if plan is None:
        return False
    await db.delete(plan)
    await db.commit()
    return True
