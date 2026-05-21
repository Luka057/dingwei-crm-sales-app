"""
Customer Transfers router(双 flow + 4 状态)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /customer-transfers                  Sales sales_request / Manager manager_direct
- GET /customer-transfers?status            Sales 自己发起 / Manager 下属发的待审
- PUT /customer-transfers/{id}/approve      **manager-only** + 必须直属下属发起的
- PUT /customer-transfers/{id}/reject       **manager-only**

§3.5.6 状态机:
  manager_direct: 后端代码一步 → executed
  sales_request:  pending → approved/rejected → executed
                  (1A 不允许 Sales 撤销 — Q3 决议)

§3.5.4 边界 case #6 客户转移并发:
  乐观锁 UPDATE customer SET owner_id=:new WHERE id=:cid AND owner_id=:old_owner
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DBSession, ManagerUser
from app.schemas.transfer import CustomerTransferCreate, CustomerTransferOut

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
    """flow 合法性校验:
    - sales_request:必须 Sales 调,且 customer.owner_id == current_user.id
    - manager_direct:必须 Manager 调,且 customer 属于其下属
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.7 — transfers module)",
    )


@router.get(
    "/",
    response_model=list[CustomerTransferOut],
    summary="转移列表(Sales 自己发起 / Manager 下属发的待审)",
)
async def list_transfers(
    user: CurrentUser,
    db: DBSession,
    status_filter: str | None = Query(None, alias="status"),
) -> list[CustomerTransferOut]:
    """Sales:WHERE initiated_by_user_id = current_user.id
    Manager:WHERE flow='sales_request' AND status='pending'
            AND from_user_id IN (SELECT id FROM user WHERE manager_id = current_user.id)
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.7 — transfers module)",
    )


@router.put(
    "/{transfer_id}/approve",
    response_model=CustomerTransferOut,
    summary="批准转移(manager-only,事务更新 customer.owner_id)",
)
async def approve_transfer(
    transfer_id: UUID, manager: ManagerUser, db: DBSession
) -> CustomerTransferOut:
    """事务:
    1. 锁 transfer 行,验证 status=pending、flow=sales_request、from_user 是 manager 直属
    2. 乐观锁更新 customer.owner_id
       UPDATE customer SET owner_id=:new WHERE id=:cid AND owner_id=:old_owner
       影响 0 行 → 409 conflict(并发被插队)
    3. transfer: status=executed, reviewed_at=now, reviewed_by=manager
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.7 — transfers module)",
    )


@router.put(
    "/{transfer_id}/reject",
    response_model=CustomerTransferOut,
    summary="拒绝转移(manager-only)",
)
async def reject_transfer(
    transfer_id: UUID, manager: ManagerUser, db: DBSession
) -> CustomerTransferOut:
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.7 — transfers module)",
    )
