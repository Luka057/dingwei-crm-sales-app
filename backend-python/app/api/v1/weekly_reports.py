"""
Weekly Reports router(状态机 draft → submitted → reopened)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- GET /weekly-reports                Sales/Manager 自己的
- GET /weekly-reports/{id}           owner OR manager 看下属 submitted/reopened
- POST /weekly-reports               创建,默认 draft
- PUT /weekly-reports/{id}           仅 draft/reopened 可编
- POST /weekly-reports/{id}/submit   draft|reopened → submitted(无审批)
- POST /weekly-reports/{id}/reopen   **manager-only**:submitted → reopened
- POST /weekly-reports/generate-ai-draft  stub(Q6 决议)
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DBSession, ManagerUser
from app.schemas.weekly_report import (
    GenerateAiDraftResponse,
    WeeklyReportCreate,
    WeeklyReportOut,
    WeeklyReportUpdate,
)
from app.services import weekly_report_service
from app.services.weekly_report_service import WeeklyReportError

router = APIRouter(prefix="/weekly-reports", tags=["weekly-reports"])


@router.get("/", response_model=list[WeeklyReportOut], summary="周报列表(自己)")
async def list_weekly_reports(
    user: CurrentUser, db: DBSession
) -> list[WeeklyReportOut]:
    return await weekly_report_service.list_my_reports(db, user)


# 路由顺序:静态路径(/generate-ai-draft)必须在动态路径({report_id})之前
@router.post(
    "/generate-ai-draft",
    response_model=GenerateAiDraftResponse,
    summary="AI 生成周报草稿(1A stub)",
)
async def generate_ai_draft(
    user: CurrentUser, db: DBSession
) -> GenerateAiDraftResponse:
    """1A stub 固定文案;Phase 1B 接 DeepSeek。"""
    return GenerateAiDraftResponse(
        summary=(
            "本周完成拜访 X 次(stub 数据)。重点客户进展正常,主要客户群"
            "对样板反馈积极。AI 草稿示例 — Phase 1B 真接入 DeepSeek 后替换。"
        ),
        next_plan=(
            "下周计划继续推进重点客户跟进,完成 2-3 个样板确认,"
            "处理 1-2 个新询盘。"
        ),
        notes="无特别事项。",
        attachments=[],
    )


@router.get(
    "/{report_id}",
    response_model=WeeklyReportOut,
    summary="周报详情(owner 或主管看下属 submitted/reopened)",
)
async def get_weekly_report(
    report_id: UUID, user: CurrentUser, db: DBSession
) -> WeeklyReportOut:
    out = await weekly_report_service.get_report(db, user, report_id)
    if out is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Weekly report not found or not accessible",
        )
    return out


@router.post(
    "/",
    response_model=WeeklyReportOut,
    status_code=status.HTTP_201_CREATED,
    summary="新建周报(默认 draft)",
)
async def create_weekly_report(
    payload: WeeklyReportCreate, user: CurrentUser, db: DBSession
) -> WeeklyReportOut:
    try:
        return await weekly_report_service.create_report(db, user, payload)
    except WeeklyReportError as exc:
        raise HTTPException(exc.code, exc.msg) from exc


@router.put(
    "/{report_id}",
    response_model=WeeklyReportOut,
    summary="编辑周报(仅 draft/reopened)",
)
async def update_weekly_report(
    report_id: UUID,
    payload: WeeklyReportUpdate,
    user: CurrentUser,
    db: DBSession,
) -> WeeklyReportOut:
    try:
        out = await weekly_report_service.update_report(db, user, report_id, payload)
    except WeeklyReportError as exc:
        raise HTTPException(exc.code, exc.msg) from exc
    if out is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Weekly report not found or not owned",
        )
    return out


@router.post(
    "/{report_id}/submit",
    response_model=WeeklyReportOut,
    summary="提交周报(draft|reopened → submitted,无审批)",
)
async def submit_weekly_report(
    report_id: UUID, user: CurrentUser, db: DBSession
) -> WeeklyReportOut:
    try:
        out = await weekly_report_service.submit_report(db, user, report_id)
    except WeeklyReportError as exc:
        raise HTTPException(exc.code, exc.msg) from exc
    if out is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Weekly report not found or not owned",
        )
    return out


@router.post(
    "/{report_id}/reopen",
    response_model=WeeklyReportOut,
    summary="退回周报(submitted → reopened,manager-only,非拒绝)",
)
async def reopen_weekly_report(
    report_id: UUID, manager: ManagerUser, db: DBSession
) -> WeeklyReportOut:
    try:
        out = await weekly_report_service.reopen_report(db, manager, report_id)
    except WeeklyReportError as exc:
        raise HTTPException(exc.code, exc.msg) from exc
    if out is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Weekly report not found or salesperson not your subordinate",
        )
    return out
