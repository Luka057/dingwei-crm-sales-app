"""Pydantic v2 DTO 聚合入口。"""

from app.schemas.ai import (
    AiBoardSearchMatch,
    AiBoardSearchRequest,
    AiBoardSearchResponse,
    AiChatCard,
    AiChatRequest,
    AiChatResponse,
)
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.schemas.common import APIModel, ErrorDetail, Paginated
from app.schemas.customer import (
    CustomerDetail,
    CustomerKPI,
    CustomerListItem,
    OverdueSummary,
    VisitTimelineItem,
)
from app.schemas.manager import SubordinateRow, SubordinateVisitItem, TeamSummary
from app.schemas.plan import (
    CalendarDay,
    CalendarResponse,
    PlanCreate,
    PlanItem,
    PlanUpdate,
)
from app.schemas.transfer import CustomerTransferCreate, CustomerTransferOut
from app.schemas.visit_record import (
    VisitAttachmentOut,
    VisitRecordCreate,
    VisitRecordOut,
)
from app.schemas.weekly_report import (
    GenerateAiDraftResponse,
    WeeklyReportBase,
    WeeklyReportCreate,
    WeeklyReportOut,
    WeeklyReportUpdate,
)

__all__ = [
    "APIModel",
    "AiBoardSearchMatch",
    "AiBoardSearchRequest",
    "AiBoardSearchResponse",
    "AiChatCard",
    "AiChatRequest",
    "AiChatResponse",
    "CalendarDay",
    "CalendarResponse",
    "CustomerDetail",
    "CustomerKPI",
    "CustomerListItem",
    "CustomerTransferCreate",
    "CustomerTransferOut",
    "ErrorDetail",
    "GenerateAiDraftResponse",
    "LoginRequest",
    "LoginResponse",
    "OverdueSummary",
    "Paginated",
    "PlanCreate",
    "PlanItem",
    "PlanUpdate",
    "SubordinateRow",
    "SubordinateVisitItem",
    "TeamSummary",
    "UserInfo",
    "VisitAttachmentOut",
    "VisitRecordCreate",
    "VisitRecordOut",
    "VisitTimelineItem",
    "WeeklyReportBase",
    "WeeklyReportCreate",
    "WeeklyReportOut",
    "WeeklyReportUpdate",
]
