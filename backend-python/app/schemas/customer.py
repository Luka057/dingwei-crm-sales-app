"""客户相关 DTO — 对齐 docs/接口文档.md §6-7 + §3.5 端点矩阵。"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.models.customer import CustomerLevel, CustomerStatus
from app.schemas.common import APIModel


class CustomerListItem(APIModel):
    """GET /customers 列表项。"""

    id: UUID
    name: str
    short_name: str | None = None
    level: CustomerLevel
    contact_name: str | None = None
    phone: str | None = None
    last_visit_at: datetime | None = None
    is_overdue: bool = False  # 运行时计算,非数据库字段
    tags: list[str] = Field(default_factory=list)  # ['overdue', 'sample', 'week'] 等


class CustomerKPI(APIModel):
    """客户 360 顶部 KPI 卡。"""

    visits: int = 0
    samples: int = 0
    orders: int = 0      # 1A 始终 0(Phase 2 接入)
    conversion_rate: float = 0.0


class VisitTimelineItem(APIModel):
    """客户 360 拜访时间线项(精简,展开时另查)。"""

    id: UUID
    visit_at: datetime
    method: str
    intention: str
    target_person: str | None = None
    content_preview: str | None = None  # content 前 60 字符
    has_attachments: bool = False
    ai_summary: str | None = None


class CustomerDetail(APIModel):
    """GET /customers/{id} 完整资料。"""

    id: UUID
    name: str
    short_name: str | None = None
    level: CustomerLevel
    ai_score: Decimal | None = None
    status: CustomerStatus
    owner_id: UUID
    contact_name: str | None = None
    contact_title: str | None = None
    phone: str | None = None
    address: str | None = None
    last_visit_at: datetime | None = None
    is_overdue: bool = False
    created_at: datetime
    kpis: CustomerKPI
    visit_records: list[VisitTimelineItem] = Field(default_factory=list)


class OverdueSummary(APIModel):
    """GET /customers/overdue-summary — 首屏提醒用,Q1 决议中日历顶部组件消费。"""

    count: int  # 今日超期总数
    items: list[CustomerListItem] = Field(default_factory=list, max_length=5)  # 前 5 详情
