"""周报 DTO — 对齐 §4.2 / §5.5 / §3.5.6 状态机。

周报 4 段固定结构(§4.2):
  ① summary    本周工作总结
  ② next_plan  下周工作计划(与 plan 表不同步,§5.5)
  ③ notes      备注事项
  ④ attachments(1A 字段保留,不开 UI)
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.weekly_report import WeeklyReportStatus
from app.schemas.common import APIModel


class WeeklyReportBase(APIModel):
    """4 段共享 schema。"""

    summary: str | None = None
    next_plan: str | None = None
    notes: str | None = None
    attachments: list[Any] | None = None  # JSON 透传,1A 不验证 schema


class WeeklyReportCreate(WeeklyReportBase):
    """POST /weekly-reports。

    week_start 通常前端不传(后端按 server 当前时间算 ISO 周一);
    试点期允许前端覆盖,便于补录历史。
    """

    week_start: date | None = None


class WeeklyReportUpdate(WeeklyReportBase):
    """PUT /weekly-reports/{id}。仅 draft / reopened 状态可编。"""


class WeeklyReportOut(APIModel):
    """周报详情 + 列表项共用。"""

    id: UUID
    salesperson_id: UUID
    salesperson_name: str | None = None  # join user.name(主管看下属时填)
    week_start: date
    summary: str | None = None
    next_plan: str | None = None
    notes: str | None = None
    attachments: list[Any] | None = None
    status: WeeklyReportStatus
    created_at: datetime
    updated_at: datetime


class GenerateAiDraftResponse(WeeklyReportBase):
    """POST /weekly-reports/generate-ai-draft 响应。

    1A stub 返回固定文本;Phase 1B 接 DeepSeek 时:
      输入聚合:当周 visit_record + 当周 plan + 当周 sample 变化
      输出:符合 4 段结构的草稿
    详见 §6.1。
    """
