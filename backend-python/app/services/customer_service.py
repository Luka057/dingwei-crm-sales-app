"""
Customer service.

引用:
- §3.5.3 数据可见性硬规则:WHERE owner_id = current_user.id
- §5.2 超期判定:A 14d / B 30d / C 60d,运行时计算,不存表
- §3.5.4 边界 case #1:Manager 本人调用也返回本人客户,不污染下属

last_visit_at IS NULL 视为"已超期"(从未拜访 = 无穷多天未拜访)。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer, CustomerLevel
from app.models.sample import Sample
from app.models.visit_attachment import VisitAttachment
from app.models.visit_record import VisitRecord
from app.schemas.customer import (
    CustomerDetail,
    CustomerKPI,
    CustomerListItem,
    OverdueSummary,
    VisitTimelineItem,
)

if TYPE_CHECKING:
    from app.core.deps import AuthUser


# A 14d / B 30d / C 60d
OVERDUE_DAYS: dict[CustomerLevel, int] = {
    CustomerLevel.A: 14,
    CustomerLevel.B: 30,
    CustomerLevel.C: 60,
}


def _now_utc_naive() -> datetime:
    """SQL Server DATETIME2 列存的是 naive UTC,这里也用 naive 比较。"""
    return datetime.utcnow()


def _is_overdue(level: CustomerLevel, last_visit_at: datetime | None) -> bool:
    """运行时计算超期。

    NULL last_visit_at 算 overdue(从未拜访 = 永远超期)。
    """
    if last_visit_at is None:
        return True
    threshold = OVERDUE_DAYS[level]
    return _now_utc_naive() - last_visit_at > timedelta(days=threshold)


def _build_tags(level: CustomerLevel, is_overdue: bool, has_active_sample: bool) -> list[str]:
    """客户卡片 tags(原型预留:overdue / sample / week)。"""
    tags: list[str] = []
    if is_overdue:
        tags.append("overdue")
    if has_active_sample:
        tags.append("sample")
    if level == CustomerLevel.A:
        tags.append("a")  # 对齐前端筛选 chip data-customer-filter="a"(原 "a-level" 与前端不匹配)
    return tags


def _to_list_item(c: Customer, is_overdue: bool, tags: list[str] | None = None) -> CustomerListItem:
    return CustomerListItem(
        id=c.id,
        name=c.name,
        short_name=c.short_name,
        level=c.level,
        contact_name=c.contact_name,
        phone=c.phone,
        last_visit_at=c.last_visit_at,
        is_overdue=is_overdue,
        tags=tags or [],
    )


# ── List ────────────────────────────────────────────────────────


async def list_customers(
    db: AsyncSession,
    user: "AuthUser",
    keyword: str | None = None,
    level: str | None = None,
    overdue: bool | None = None,
) -> list[CustomerListItem]:
    """筛选自己的客户。

    overdue 筛选在 Python 侧完成(运行时计算,SQL 难直接表达 A/B/C 不同阈值)。
    """
    stmt = select(Customer).where(Customer.owner_id == UUID(user.id))
    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Customer.name.like(pattern),
                Customer.short_name.like(pattern),
            )
        )
    if level:
        stmt = stmt.where(Customer.level == level)

    # SQL Server 不支持 IS NULL 直接在 ORDER BY 当布尔表达式,用 CASE 表达
    # NULL last_visit_at(从未拜访)排最前,然后按 last_visit_at 倒序
    from sqlalchemy import case
    null_first = case((Customer.last_visit_at.is_(None), 0), else_=1)
    result = await db.execute(
        stmt.order_by(null_first, Customer.last_visit_at.desc())
    )
    customers = result.scalars().all()

    items: list[CustomerListItem] = []
    for c in customers:
        is_overdue = _is_overdue(c.level, c.last_visit_at)
        if overdue is True and not is_overdue:
            continue
        if overdue is False and is_overdue:
            continue
        items.append(_to_list_item(c, is_overdue, _build_tags(c.level, is_overdue, False)))
    return items


# ── Detail ──────────────────────────────────────────────────────


async def get_customer_detail(
    db: AsyncSession,
    user: "AuthUser",
    customer_id: UUID,
) -> CustomerDetail | None:
    """客户 360 详情。

    返回 None 表示客户不存在 OR 不属于当前用户(调用方统一 404,防探测)。
    """
    stmt = select(Customer).where(
        Customer.id == customer_id,
        Customer.owner_id == UUID(user.id),
    )
    customer = (await db.execute(stmt)).scalar_one_or_none()
    if customer is None:
        return None

    # KPI 聚合
    visits_count = await db.scalar(
        select(func.count())
        .select_from(VisitRecord)
        .where(VisitRecord.customer_id == customer_id)
    ) or 0
    samples_count = await db.scalar(
        select(func.count())
        .select_from(Sample)
        .where(Sample.customer_id == customer_id)
    ) or 0

    # 1A orders / conversion_rate 始终 0(Phase 2 接入后补)
    kpi = CustomerKPI(
        visits=visits_count,
        samples=samples_count,
        orders=0,
        conversion_rate=0.0,
    )

    # Timeline 前 20 条
    timeline_stmt = (
        select(VisitRecord)
        .where(VisitRecord.customer_id == customer_id)
        .order_by(VisitRecord.visit_at.desc())
        .limit(20)
    )
    visits = (await db.execute(timeline_stmt)).scalars().all()

    # 批量查每个 visit 是否有附件(避免 N+1,但 1A 简单做)
    visit_ids = [v.id for v in visits]
    visit_with_attach: set[UUID] = set()
    if visit_ids:
        attach_stmt = (
            select(VisitAttachment.visit_record_id)
            .where(VisitAttachment.visit_record_id.in_(visit_ids))
            .distinct()
        )
        for (vid,) in (await db.execute(attach_stmt)).all():
            visit_with_attach.add(vid)

    timeline = [
        VisitTimelineItem(
            id=v.id,
            visit_at=v.visit_at,
            method=v.method.value,
            intention=v.intention.value,
            target_person=v.target_person,
            content_preview=(v.content[:60] + "..." if v.content and len(v.content) > 60 else v.content),
            has_attachments=v.id in visit_with_attach,
            ai_summary=v.ai_summary,
        )
        for v in visits
    ]

    return CustomerDetail(
        id=customer.id,
        name=customer.name,
        short_name=customer.short_name,
        level=customer.level,
        ai_score=customer.ai_score,
        status=customer.status,
        owner_id=customer.owner_id,
        contact_name=customer.contact_name,
        contact_title=customer.contact_title,
        phone=customer.phone,
        address=customer.address,
        last_visit_at=customer.last_visit_at,
        is_overdue=_is_overdue(customer.level, customer.last_visit_at),
        created_at=customer.created_at,
        kpis=kpi,
        visit_records=timeline,
    )


# ── Overdue Summary ─────────────────────────────────────────────


async def get_overdue_summary(
    db: AsyncSession,
    user: "AuthUser",
) -> OverdueSummary:
    """今日超期客户摘要(首屏提醒用,Q1 决议中日历顶部组件消费)。"""
    stmt = select(Customer).where(Customer.owner_id == UUID(user.id))
    result = await db.execute(stmt)
    customers = result.scalars().all()

    overdue_list = [
        (c, _is_overdue(c.level, c.last_visit_at))
        for c in customers
    ]
    overdue_only = [c for c, ov in overdue_list if ov]
    # 按 level (A > B > C) + last_visit_at 升序(越久没拜访越前)排
    level_priority = {CustomerLevel.A: 0, CustomerLevel.B: 1, CustomerLevel.C: 2}
    overdue_only.sort(
        key=lambda c: (
            level_priority[c.level],
            c.last_visit_at or datetime.min,
        )
    )

    items = [
        _to_list_item(c, True, _build_tags(c.level, True, False))
        for c in overdue_only[:5]
    ]
    return OverdueSummary(count=len(overdue_only), items=items)
