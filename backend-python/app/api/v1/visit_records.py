"""
Visit Records router.

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /visit-records   salesperson_id 强制 = current_user.id
"""

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.visit_record import VisitRecordCreate, VisitRecordOut
from app.services import visit_record_service
from app.services.visit_record_service import VisitError

router = APIRouter(prefix="/visit-records", tags=["visit-records"])


@router.post(
    "/",
    response_model=VisitRecordOut,
    status_code=status.HTTP_201_CREATED,
    summary="新建拜访记录(事务:绑 attachment + 更新 last_visit_at)",
)
async def create_visit_record(
    payload: VisitRecordCreate,
    user: CurrentUser,
    db: DBSession,
) -> VisitRecordOut:
    try:
        return await visit_record_service.create_visit_record(db, user, payload)
    except VisitError as exc:
        raise HTTPException(exc.code, exc.msg) from exc
