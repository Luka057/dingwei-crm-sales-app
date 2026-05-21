"""
Manager router(manager-only,主管视角)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- GET /manager/team-summary                  **manager-only**
- GET /manager/subordinates/{userId}/visits  **manager-only** + manager_id 校验
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DBSession, ManagerUser
from app.schemas.common import Paginated
from app.schemas.manager import SubordinateVisitItem, TeamSummary
from app.services import manager_service

router = APIRouter(prefix="/manager", tags=["manager"])


@router.get(
    "/team-summary",
    response_model=TeamSummary,
    summary="团队概览(顶部聚合 + 下属逐行)",
)
async def team_summary(manager: ManagerUser, db: DBSession) -> TeamSummary:
    return await manager_service.get_team_summary(db, manager)


@router.get(
    "/subordinates/{user_id}/visits",
    response_model=Paginated[SubordinateVisitItem],
    summary="指定下属拜访明细(分页)",
)
async def subordinate_visits(
    user_id: UUID,
    manager: ManagerUser,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Paginated[SubordinateVisitItem]:
    result = await manager_service.get_subordinate_visits(
        db, manager, user_id, page=page, size=size
    )
    if result is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "User not found or not your subordinate",
        )
    return result
