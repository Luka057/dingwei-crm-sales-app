"""拜访记录 + 照片附件 DTO。"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.visit_attachment import AttachmentType
from app.models.visit_record import VisitIntention, VisitMethod
from app.schemas.common import APIModel


class VisitAttachmentOut(APIModel):
    """POST /uploads/visit-photo 返回 + 拜访记录嵌套返回。

    storage_path 用于前端拼访问 URL(GET /uploads/visit-photo/{id})。
    """

    id: UUID
    type: AttachmentType
    storage_path: str
    file_size: int
    mime_type: str
    uploaded_at: datetime


class VisitRecordCreate(APIModel):
    """POST /visit-records 请求体。

    attachment_ids:前端先调 /uploads/visit-photo 拿 id,再带在这里。
    """

    customer_id: UUID
    visit_at: datetime
    method: VisitMethod
    intention: VisitIntention = VisitIntention.NONE
    target_person: str | None = Field(default=None, max_length=64)
    target_title: str | None = Field(default=None, max_length=64)
    content: str | None = None
    next_follow_at: datetime | None = None
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=10)


class VisitRecordOut(APIModel):
    """POST /visit-records 响应,以及 GET /customers/{id} 时间线展开。"""

    id: UUID
    customer_id: UUID
    salesperson_id: UUID
    visit_at: datetime
    method: VisitMethod
    intention: VisitIntention
    target_person: str | None = None
    target_title: str | None = None
    content: str | None = None
    ai_summary: str | None = None
    next_follow_at: datetime | None = None
    created_at: datetime
    attachments: list[VisitAttachmentOut] = Field(default_factory=list)
