"""
Manager service(主管视图,manager-only)。

§3.5.2 端点:
- GET /manager/team-summary
- GET /manager/subordinates/{userId}/visits

§3.5.3 数据可见性硬规则:
- 看下属拜访 / plan 时,自动过滤 is_personal=True(plan)
  (visit_record 表本身无 is_personal,主管看的是实际拜访 — 这条天然不漏)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer, CustomerLevel
from app.models.customer_transfer import CustomerTransfer, TransferFlow, TransferStatus
from app.models.user import User
from app.models.visit_attachment import VisitAttachment
from app.models.visit_record import VisitRecord
from app.schemas.common import Paginated
from app.schemas.manager import SubordinateRow, SubordinateVisitItem, TeamSummary
from app.services.customer_service import _is_overdue, _now_utc_naive

if TYPE_CHECKING:
    from app.core.deps import AuthUser


def _iso_week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    """返回 (本周一 00:00, 本周日 23:59:59)。"""
    now = now or _now_utc_naive()
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sunday_end = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return monday, sunday_end


# ── Team Summary ────────────────────────────────────────────────


async def get_team_summary(
    db: AsyncSession,
    manager: "AuthUser",
) -> TeamSummary:
    """聚合下属本周数据 + 待审转移数。"""
    current_id = UUID(manager.id)

    # 1. 下属列表
    sub_rows = (
        await db.execute(
            select(User).where(User.manager_id == current_id).order_by(User.name)
        )
    ).scalars().all()
    sub_ids = [u.id for u in sub_rows]
    if not sub_ids:
        # 没下属 — 返回空表 + 0 计数
        return TeamSummary(
            team_visits_this_week=0,
            team_overdue_customers=0,
            pending_transfers=0,
            subordinates=[],
        )

    # 2. 本周拜访 per-sub
    week_start, week_end = _iso_week_bounds()
    visits_per_sub_rows = (
        await db.execute(
            select(VisitRecord.salesperson_id, func.count())
            .where(
                VisitRecord.salesperson_id.in_(sub_ids),
                VisitRecord.visit_at >= week_start,
                VisitRecord.visit_at <= week_end,
            )
            .group_by(VisitRecord.salesperson_id)
        )
    ).all()
    visits_per_sub: dict[UUID, int] = {sid: cnt for sid, cnt in visits_per_sub_rows}

    # 3. 超期客户 per-sub(运行时计算,A14/B30/C60)
    all_customers_rows = (
        await db.execute(
            select(Customer.owner_id, Customer.level, Customer.last_visit_at).where(
                Customer.owner_id.in_(sub_ids)
            )
        )
    ).all()
    overdue_per_sub: dict[UUID, int] = {sid: 0 for sid in sub_ids}
    for owner_id, level, last_visit_at in all_customers_rows:
        if _is_overdue(level, last_visit_at):
            overdue_per_sub[owner_id] = overdue_per_sub.get(owner_id, 0) + 1

    # 4. 待审转移数(下属发起的 sales_request pending)
    pending_count = await db.scalar(
        select(func.count())
        .select_from(CustomerTransfer)
        .where(
            CustomerTransfer.flow == TransferFlow.SALES_REQUEST,
            CustomerTransfer.status == TransferStatus.PENDING,
            CustomerTransfer.from_user_id.in_(sub_ids),
        )
    ) or 0

    # 5. 聚合
    subs_dto = [
        SubordinateRow(
            user_id=u.id,
            name=u.name,
            username=u.username,
            visits_this_week=visits_per_sub.get(u.id, 0),
            overdue_customers=overdue_per_sub.get(u.id, 0),
        )
        for u in sub_rows
    ]
    team_visits = sum(s.visits_this_week for s in subs_dto)
    team_overdue = sum(s.overdue_customers for s in subs_dto)

    return TeamSummary(
        team_visits_this_week=team_visits,
        team_overdue_customers=team_overdue,
        pending_transfers=pending_count,
        subordinates=subs_dto,
    )


# ── Subordinate Visits ──────────────────────────────────────────


async def get_subordinate_visits(
    db: AsyncSession,
    manager: "AuthUser",
    subordinate_id: UUID,
    page: int = 1,
    size: int = 20,
) -> Paginated[SubordinateVisitItem] | None:
    """指定下属的拜访列表(分页)。

    返回 None 表示该 user 不是 manager 的直属下属(调用方 404)。
    """
    current_id = UUID(manager.id)

    # 校验 subordinate_id 是否本人下属
    sub_manager_id = await db.scalar(
        select(User.manager_id).where(User.id == subordinate_id)
    )
    if sub_manager_id != current_id:
        return None

    # 总数
    total = await db.scalar(
        select(func.count())
        .select_from(VisitRecord)
        .where(VisitRecord.salesperson_id == subordinate_id)
    ) or 0

    # 分页拉
    offset = (page - 1) * size
    visits = (
        await db.execute(
            select(VisitRecord, Customer.name)
            .join(Customer, VisitRecord.customer_id == Customer.id)
            .where(VisitRecord.salesperson_id == subordinate_id)
            .order_by(VisitRecord.visit_at.desc())
            .offset(offset)
            .limit(size)
        )
    ).all()

    if not visits:
        return Paginated(items=[], total=total, page=page, size=size)

    # 批量查 attachment 是否存在
    visit_ids = [v.id for v, _ in visits]
    visit_with_attach: set[UUID] = set()
    attach_rows = await db.execute(
        select(VisitAttachment.visit_record_id)
        .where(VisitAttachment.visit_record_id.in_(visit_ids))
        .distinct()
    )
    for (vid,) in attach_rows.all():
        if vid is not None:
            visit_with_attach.add(vid)

    items = [
        SubordinateVisitItem(
            id=v.id,
            customer_id=v.customer_id,
            customer_name=cname,
            visit_at=v.visit_at,
            method=v.method,
            intention=v.intention,
            target_person=v.target_person,
            content_preview=(
                v.content[:60] + "..."
                if v.content and len(v.content) > 60
                else v.content
            ),
            has_attachments=v.id in visit_with_attach,
        )
        for v, cname in visits
    ]
    return Paginated(items=items, total=total, page=page, size=size)
