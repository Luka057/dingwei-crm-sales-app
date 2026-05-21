"""
Plans router.

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- GET /plans/calendar   Sales/Manager 自己的 plan(含 is_personal)
- POST /plans           Q8 is_personal 后端推断 + 前端 toggle 可改
- PUT /plans/{id}       owner 校验
- DELETE /plans/{id}    owner 校验
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.plan import CalendarResponse, PlanCreate, PlanItem, PlanUpdate
from app.services import plan_service

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
    return await plan_service.get_calendar(db, user, year, month)


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
    try:
        return await plan_service.create_plan(db, user, payload)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc


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
    try:
        item = await plan_service.update_plan(db, user, plan_id, payload)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found or not owned")
    return item


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
    ok = await plan_service.delete_plan(db, user, plan_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Plan not found or not owned")
