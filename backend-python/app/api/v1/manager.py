"""
Manager router(manager-only,主管视角)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- GET /manager/team-summary                  **manager-only**
- GET /manager/subordinates/{userId}/visits  **manager-only** + manager_id 校验

Q1 决议:这两个端点服务于日历 tab 顶部「团队概览」卡片 +
        主管视图子页(/app/manager/team-summary)。

§3.5.3 数据可见性硬规则:Manager 看下属时 plan/visit 都自动过滤 is_personal=True
(主管不窥探下属的喝水/站立提醒)。
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DBSession, ManagerUser
from app.schemas.common import Paginated
from app.schemas.manager import SubordinateVisitItem, TeamSummary

router = APIRouter(prefix="/manager", tags=["manager"])


@router.get(
    "/team-summary",
    response_model=TeamSummary,
    summary="团队概览(顶部聚合 + 下属逐行)",
)
async def team_summary(manager: ManagerUser, db: DBSession) -> TeamSummary:
    """聚合查询:
    - subordinates = SELECT * FROM user WHERE manager_id = :manager_id
    - visits_this_week = COUNT(visit_record WHERE salesperson_id IN subs AND visit_at IN this_week)
    - team_overdue = SUM(超期计算 per sub)
    - pending_transfers = COUNT(customer_transfer WHERE flow='sales_request'
                                AND status='pending' AND from_user_id IN subs)
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.8 — manager module)",
    )


@router.get(
    "/subordinates/{user_id}/visits",
    response_model=Paginated[SubordinateVisitItem],
    summary="指定下属拜访明细(分页,自动过滤 is_personal=True)",
)
async def subordinate_visits(
    user_id: UUID,
    manager: ManagerUser,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Paginated[SubordinateVisitItem]:
    """校验:user_id 必须是 current_user.id 的直属下属
    (SELECT 1 FROM user WHERE id = :user_id AND manager_id = :current_id)。

    §3.5.3 数据可见性:visit_record 表本身无 is_personal,但本端点 join plan
    时会过滤掉 plan.is_personal=True 关联的 visit(实际上 visit 不绑 plan,
    此条规则主要影响 /manager/subordinates 的 plan 视图,后续 1B 实施时关注)。
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.8 — manager module)",
    )
