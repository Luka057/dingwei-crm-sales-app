"""主管视图 DTO — 对齐 §3.5.2 manager-only 端点 + Q1 决议。

Q1 决议:Manager 入口在日历 tab 顶部「团队概览」卡片,点击进入主管子页。
本 schema 给:
  - GET /manager/team-summary  → TeamSummary
  - GET /manager/subordinates/{userId}/visits  → Paginated[SubordinateVisitItem]
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.visit_record import VisitIntention, VisitMethod
from app.schemas.common import APIModel


class SubordinateRow(APIModel):
    """team-summary 表格里的一行下属。"""

    user_id: UUID
    name: str
    username: str
    visits_this_week: int
    overdue_customers: int


class TeamSummary(APIModel):
    """GET /manager/team-summary 响应。

    顶部聚合 + 下属逐行 + 待审转移数。前端用于日历 tab 的「团队概览」卡片。
    """

    # 顶部聚合
    team_visits_this_week: int
    team_overdue_customers: int
    pending_transfers: int

    # 下属逐行
    subordinates: list[SubordinateRow] = Field(default_factory=list)


class SubordinateVisitItem(APIModel):
    """GET /manager/subordinates/{userId}/visits 列表项。

    自动过滤 is_personal=True(§3.5.3 数据可见性硬规则)。
    """

    id: UUID
    customer_id: UUID
    customer_name: str
    visit_at: datetime
    method: VisitMethod
    intention: VisitIntention
    target_person: str | None = None
    content_preview: str | None = None
    has_attachments: bool = False
