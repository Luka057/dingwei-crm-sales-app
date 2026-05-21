"""
Weekly Reports router(状态机 draft → submitted → reopened)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- GET /weekly-reports                Sales/Manager 自己的
- GET /weekly-reports/{id}           Sales/Manager owner OR 主管看下属 submitted/reopened
- POST /weekly-reports               创建,默认 draft
- PUT /weekly-reports/{id}           仅 draft/reopened 可编
- POST /weekly-reports/{id}/submit   draft|reopened → submitted(无审批,§3.5.6)
- POST /weekly-reports/{id}/reopen   **manager-only**:submitted → reopened
- POST /weekly-reports/generate-ai-draft  stub(Q6 决议,返回 mock 4 段)

§4.2 周报覆盖范围:**当周**(非上一周)。一周一份(UQ_weekly_owner_week)。
§5.5 next_plan 与 plan 表不同步。
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

router = APIRouter(prefix="/weekly-reports", tags=["weekly-reports"])


@router.get("/", response_model=list[WeeklyReportOut], summary="周报列表(自己)")
async def list_weekly_reports(
    user: CurrentUser, db: DBSession
) -> list[WeeklyReportOut]:
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.6 — weekly-reports module)",
    )


@router.get(
    "/{report_id}",
    response_model=WeeklyReportOut,
    summary="周报详情(owner 或主管看下属 submitted/reopened)",
)
async def get_weekly_report(
    report_id: UUID, user: CurrentUser, db: DBSession
) -> WeeklyReportOut:
    """主管看下属时,只允许 status IN ('submitted', 'reopened'),draft 看不见。"""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.6 — weekly-reports module)",
    )


@router.post(
    "/",
    response_model=WeeklyReportOut,
    status_code=status.HTTP_201_CREATED,
    summary="新建周报(默认 draft)",
)
async def create_weekly_report(
    payload: WeeklyReportCreate, user: CurrentUser, db: DBSession
) -> WeeklyReportOut:
    """week_start 未传时按 server 当前时间算 ISO 周一。冲突 UQ_weekly_owner_week → 409。"""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.6 — weekly-reports module)",
    )


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
    """status 非 draft/reopened 时返 409 conflict。"""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.6 — weekly-reports module)",
    )


@router.post(
    "/{report_id}/submit",
    response_model=WeeklyReportOut,
    summary="提交周报(draft|reopened → submitted,无审批)",
)
async def submit_weekly_report(
    report_id: UUID, user: CurrentUser, db: DBSession
) -> WeeklyReportOut:
    """§3.5.6 状态机:**submit 即生效,主管能看,但不需要主管批准**。"""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.6 — weekly-reports module)",
    )


@router.post(
    "/{report_id}/reopen",
    response_model=WeeklyReportOut,
    summary="退回周报(submitted → reopened,manager-only,非拒绝)",
)
async def reopen_weekly_report(
    report_id: UUID, manager: ManagerUser, db: DBSession
) -> WeeklyReportOut:
    """**manager-only**;退回 = 让销售补,不是拒绝(§0 术语对照)。
    校验该 report 的 salesperson 的 manager_id == current manager id。
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.6 — weekly-reports module)",
    )


# ── AI 草稿(stub,§6.1) ─────────────────────────────────────────


@router.post(
    "/generate-ai-draft",
    response_model=GenerateAiDraftResponse,
    summary="AI 生成周报草稿(1A stub)",
)
async def generate_ai_draft(
    user: CurrentUser, db: DBSession
) -> GenerateAiDraftResponse:
    """1A stub 固定文案;Phase 1B 接 DeepSeek。

    Phase 1B 输入聚合:当周 visit_record + 当周 plan + 当周 sample 变化。
    输出格式:4 段(summary/next_plan/notes/attachments=[])。
    """
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
