"""
Plans router.

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- GET /plans/calendar   Sales/Manager 自己的 plan(全部含 is_personal)
- POST /plans           创建 plan,无审批立即生效(§3.5.6)
- PUT /plans/{id}       owner 校验
- DELETE /plans/{id}    owner 校验

Q8 决议:POST 时 is_personal=None 表示后端推断
  (type='custom' AND customer_id IS NULL → True)
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.plan import CalendarResponse, PlanCreate, PlanItem, PlanUpdate

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get(
    "/calendar",
    response_model=CalendarResponse,
    summary="日历视图(按月,自己的 plan 全部)",
)
async def calendar(
    user: CurrentUser,
    db: DBSession,
    year: int = Query(ge=2000, le=2100),
    month: int = Query(ge=1, le=12),
) -> CalendarResponse:
    """Sales 看自己的全部 plan(含个人提醒);Manager 调本端点也是看自己的。

    主管看下属的 plan 走 /manager/subordinates/{userId}/visits(自动 filter is_personal=0)。
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.3 — plans module)",
    )


@router.post(
    "/",
    response_model=PlanItem,
    status_code=status.HTTP_201_CREATED,
    summary="新建 plan(无审批)",
)
async def create_plan(
    payload: PlanCreate,
    user: CurrentUser,
    db: DBSession,
) -> PlanItem:
    """Q8 推断:is_personal 未传时 type='custom' AND customer_id IS NULL → True。"""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.3 — plans module)",
    )


@router.put(
    "/{plan_id}",
    response_model=PlanItem,
    summary="编辑 plan(仅 owner)",
)
async def update_plan(
    plan_id: UUID,
    payload: PlanUpdate,
    user: CurrentUser,
    db: DBSession,
) -> PlanItem:
    """WHERE salesperson_id = current_user.id 强制 owner。"""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.3 — plans module)",
    )


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除 plan(仅 owner)",
)
async def delete_plan(
    plan_id: UUID,
    user: CurrentUser,
    db: DBSession,
) -> None:
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.3 — plans module)",
    )
