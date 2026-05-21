"""Plan 相关 DTO — 对齐 docs/接口文档.md §2-5 + §3.5.5 Q8 决议。"""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from app.models.plan import PlanStatus, PlanType
from app.schemas.common import APIModel


class PlanItem(APIModel):
    """日历列表项,GET /plans/calendar 嵌套在 days[].items[] 里。"""

    id: UUID
    type: PlanType
    customer_id: UUID | None = None
    customer_name: str | None = None  # join 客户表后填充
    title: str
    scheduled_at: datetime
    status: PlanStatus
    is_personal: bool = False  # Manager 视图过滤的依据
    content: str | None = None


class CalendarDay(APIModel):
    date: date
    items: list[PlanItem] = Field(default_factory=list)


class CalendarResponse(APIModel):
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    days: list[CalendarDay] = Field(default_factory=list)


class PlanCreate(APIModel):
    """POST /plans 请求体。

    Q8 决议:is_personal 后端推断 + 前端 toggle 可改:
    - is_personal=None(未传):后端推断,type='custom' AND customer_id IS None → True
    - is_personal=True/False:前端显式 override
    """

    type: PlanType
    customer_id: UUID | None = None
    title: str = Field(min_length=1, max_length=128)
    scheduled_at: datetime
    content: str | None = None
    is_personal: bool | None = None  # 关键:三态(None = 后端推断)


class PlanUpdate(APIModel):
    """PUT /plans/{id} 请求体。可部分更新。"""

    type: PlanType | None = None
    customer_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=128)
    scheduled_at: datetime | None = None
    content: str | None = None
    status: PlanStatus | None = None
    is_personal: bool | None = None
