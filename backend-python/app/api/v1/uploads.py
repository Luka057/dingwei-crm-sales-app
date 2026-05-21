"""
Uploads router(Q7 决议:照片上传完整可用)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /uploads/visit-photo       Sales/Manager 上传(per-user 限速)
- GET /uploads/visit-photo/{id}   Sales(owner) / Manager(owner 或下属上传)
"""

from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.core.deps import CurrentUser, DBSession
from app.schemas.visit_record import VisitAttachmentOut
from app.services import upload_service
from app.services.upload_service import UploadError

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "/visit-photo",
    response_model=VisitAttachmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="上传拜访照片",
)
async def upload_visit_photo(
    user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),  # noqa: B008
) -> VisitAttachmentOut:
    content = await file.read()
    try:
        return await upload_service.save_visit_photo(db, user, content)
    except UploadError as exc:
        raise HTTPException(exc.code, exc.msg) from exc


@router.get(
    "/visit-photo/{attachment_id}",
    response_class=FileResponse,
    summary="查看拜访照片(JWT + owner/manager 鉴权)",
)
async def get_visit_photo(
    attachment_id: UUID,
    user: CurrentUser,
    db: DBSession,
) -> FileResponse:
    result = await upload_service.get_visit_photo_path(db, user, attachment_id)
    if result is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Photo not found or not accessible",
        )
    path, mime_type = result
    return FileResponse(path, media_type=mime_type)
