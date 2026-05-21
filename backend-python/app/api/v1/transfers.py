"""
Customer Transfers router(双 flow + 4 状态)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /customer-transfers                  Sales sales_request / Manager manager_direct
- GET /customer-transfers?status            Sales 自己 / Manager 下属待审
- PUT /customer-transfers/{id}/approve      **manager-only**
- PUT /customer-transfers/{id}/reject       **manager-only**
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DBSession, ManagerUser
from app.schemas.transfer import CustomerTransferCreate, CustomerTransferOut
from app.services import transfer_service
from app.services.transfer_service import TransferError

router = APIRouter(prefix="/customer-transfers", tags=["transfers"])


@router.post(
    "/",
    response_model=CustomerTransferOut,
    status_code=status.HTTP_201_CREATED,
    summary="发起客户转移(flow 决定行为)",
)
async def create_transfer(
    payload: CustomerTransferCreate,
    user: CurrentUser,
    db: DBSession,
) -> CustomerTransferOut:
    try:
        return await transfer_service.create_transfer(db, user, payload)
    except TransferError as exc:
        raise HTTPException(exc.code, exc.msg) from exc


@router.get(
    "/",
    response_model=list[CustomerTransferOut],
    summary="转移列表(Sales 自己 / Manager 下属待审)",
)
async def list_transfers(
    user: CurrentUser,
    db: DBSession,
    status_filter: str | None = Query(None, alias="status"),
) -> list[CustomerTransferOut]:
    return await transfer_service.list_transfers(db, user, status_filter=status_filter)


@router.put(
    "/{transfer_id}/approve",
    response_model=CustomerTransferOut,
    summary="批准转移(manager-only,事务乐观锁更新 owner_id)",
)
async def approve_transfer(
    transfer_id: UUID, manager: ManagerUser, db: DBSession
) -> CustomerTransferOut:
    try:
        out = await transfer_service.approve_transfer(db, manager, transfer_id)
    except TransferError as exc:
        raise HTTPException(exc.code, exc.msg) from exc
    if out is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Transfer not found or not your subordinate's request",
        )
    return out


@router.put(
    "/{transfer_id}/reject",
    response_model=CustomerTransferOut,
    summary="拒绝转移(manager-only)",
)
async def reject_transfer(
    transfer_id: UUID, manager: ManagerUser, db: DBSession
) -> CustomerTransferOut:
    try:
        out = await transfer_service.reject_transfer(db, manager, transfer_id)
    except TransferError as exc:
        raise HTTPException(exc.code, exc.msg) from exc
    if out is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Transfer not found or not your subordinate's request",
        )
    return out
