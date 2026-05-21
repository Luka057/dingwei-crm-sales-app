"""
VisitRecord service.

事务保证(§3.5.4 边界 case 实现):
  1. 验证 customer.owner_id == current_user.id
  2. 验证 attachment_ids 都属于 current(uploader_id)且未绑定
  3. INSERT visit_record(salesperson_id=current_user.id)
  4. UPDATE visit_attachment SET visit_record_id=:vid WHERE id IN (...)
  5. UPDATE customer SET last_visit_at = greatest(last_visit_at, visit_at)
  全部一个事务,任一失败回滚。
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.visit_attachment import VisitAttachment
from app.models.visit_record import VisitRecord
from app.schemas.visit_record import (
    VisitAttachmentOut,
    VisitRecordCreate,
    VisitRecordOut,
)

if TYPE_CHECKING:
    from app.core.deps import AuthUser


class VisitError(Exception):
    """业务级拜访错误,调用方转 HTTP 4xx。"""

    def __init__(self, code: int, msg: str) -> None:
        super().__init__(msg)
        self.code = code
        self.msg = msg


async def create_visit_record(
    db: AsyncSession,
    user: "AuthUser",
    payload: VisitRecordCreate,
) -> VisitRecordOut:
    """事务创建拜访记录 + 绑定 attachments + 更新 last_visit_at。"""
    current_id = UUID(user.id)

    # 1. 校验 customer owner
    customer = (
        await db.execute(
            select(Customer).where(
                Customer.id == payload.customer_id,
                Customer.owner_id == current_id,
            )
        )
    ).scalar_one_or_none()
    if customer is None:
        raise VisitError(404, "customer not found or not owned by current user")

    # 2. 校验 attachment_ids(若有):必须属于本人 + 未绑定 visit
    if payload.attachment_ids:
        stmt = select(VisitAttachment).where(
            VisitAttachment.id.in_(payload.attachment_ids)
        )
        attachments = (await db.execute(stmt)).scalars().all()
        if len(attachments) != len(payload.attachment_ids):
            raise VisitError(400, "some attachment_ids not found")
        for att in attachments:
            if att.uploader_id != current_id:
                raise VisitError(403, f"attachment {att.id} not uploaded by current user")
            if att.visit_record_id is not None:
                raise VisitError(409, f"attachment {att.id} already bound to a visit")

    # 3. INSERT visit_record
    visit = VisitRecord(
        customer_id=payload.customer_id,
        salesperson_id=current_id,
        visit_at=payload.visit_at,
        method=payload.method,
        intention=payload.intention,
        target_person=payload.target_person,
        target_title=payload.target_title,
        content=payload.content,
        next_follow_at=payload.next_follow_at,
    )
    db.add(visit)
    await db.flush()  # 拿到 visit.id

    # 4. 绑 attachments
    if payload.attachment_ids:
        await db.execute(
            update(VisitAttachment)
            .where(VisitAttachment.id.in_(payload.attachment_ids))
            .values(visit_record_id=visit.id)
        )

    # 5. 更新 customer.last_visit_at(只在新值更新时)
    if customer.last_visit_at is None or payload.visit_at > customer.last_visit_at:
        customer.last_visit_at = payload.visit_at

    await db.commit()
    await db.refresh(visit)

    # 收集绑好的 attachment(回包给前端)
    attachment_outs: list[VisitAttachmentOut] = []
    if payload.attachment_ids:
        bound = (
            await db.execute(
                select(VisitAttachment).where(
                    VisitAttachment.visit_record_id == visit.id
                )
            )
        ).scalars().all()
        attachment_outs = [
            VisitAttachmentOut(
                id=a.id,
                type=a.type,
                storage_path=a.storage_path,
                file_size=a.file_size,
                mime_type=a.mime_type,
                uploaded_at=a.uploaded_at,
            )
            for a in bound
        ]

    return VisitRecordOut(
        id=visit.id,
        customer_id=visit.customer_id,
        salesperson_id=visit.salesperson_id,
        visit_at=visit.visit_at,
        method=visit.method,
        intention=visit.intention,
        target_person=visit.target_person,
        target_title=visit.target_title,
        content=visit.content,
        ai_summary=visit.ai_summary,
        next_follow_at=visit.next_follow_at,
        created_at=visit.created_at,
        attachments=attachment_outs,
    )
