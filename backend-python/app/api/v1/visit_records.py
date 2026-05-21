"""
Visit Records router.

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /visit-records   salesperson_id 强制 = current_user.id

实施:同事务更新 customer.last_visit_at(超期判定依据)。
attachment_ids 关联已通过 POST /uploads/visit-photo 上传的 visit_attachment。
"""

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.visit_record import VisitRecordCreate, VisitRecordOut

router = APIRouter(prefix="/visit-records", tags=["visit-records"])


@router.post(
    "/",
    response_model=VisitRecordOut,
    status_code=status.HTTP_201_CREATED,
    summary="新建拜访记录(现场实时录入)",
)
async def create_visit_record(
    payload: VisitRecordCreate,
    user: CurrentUser,
    db: DBSession,
) -> VisitRecordOut:
    """事务:
    1. 验证 customer.owner_id == current_user.id
    2. 验证 attachment_ids 都属于本人上传的(未关联其他 visit_record)
    3. INSERT visit_record(salesperson_id=current_user.id)
    4. 关联 visit_attachment(set visit_record_id)
    5. UPDATE customer SET last_visit_at = max(last_visit_at, visit_at) WHERE id=...
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.4 — visits module)",
    )
