"""
ORM 模型聚合入口。

import 所有模型让 SQLAlchemy 注册到 Base.metadata,
供 Alembic env.py 通过 target_metadata 自动发现。
"""

from app.db.base import Base
from app.models.customer import Customer, CustomerLevel, CustomerStatus
from app.models.customer_transfer import (
    CustomerTransfer,
    TransferFlow,
    TransferStatus,
)
from app.models.plan import Plan, PlanStatus, PlanType
from app.models.sample import Sample, SampleStatus
from app.models.user import User, UserRole, UserStatus
from app.models.visit_attachment import AttachmentType, VisitAttachment
from app.models.visit_record import VisitIntention, VisitMethod, VisitRecord
from app.models.weekly_report import WeeklyReport, WeeklyReportStatus

__all__ = [
    "AttachmentType",
    "Base",
    "Customer",
    "CustomerLevel",
    "CustomerStatus",
    "CustomerTransfer",
    "Plan",
    "PlanStatus",
    "PlanType",
    "Sample",
    "SampleStatus",
    "TransferFlow",
    "TransferStatus",
    "User",
    "UserRole",
    "UserStatus",
    "VisitAttachment",
    "VisitIntention",
    "VisitMethod",
    "VisitRecord",
    "WeeklyReport",
    "WeeklyReportStatus",
]
