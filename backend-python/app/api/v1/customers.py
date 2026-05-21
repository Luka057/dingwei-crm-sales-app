"""
Customers router(含 overdue-summary)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- GET /customers              Sales/Manager 看自己的(owner_id 过滤)
- GET /customers/{id}         Sales/Manager owner 校验
- GET /customers/overdue-summary  Sales/Manager 自己的超期客户
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.customer import CustomerDetail, CustomerListItem, OverdueSummary
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get(
    "/",
    response_model=list[CustomerListItem],
    summary="客户列表(自己的)",
)
async def list_customers(
    user: CurrentUser,
    db: DBSession,
    keyword: str | None = None,
    level: str | None = None,
    overdue: bool | None = None,
) -> list[CustomerListItem]:
    return await customer_service.list_customers(
        db, user, keyword=keyword, level=level, overdue=overdue
    )


@router.get(
    "/overdue-summary",
    response_model=OverdueSummary,
    summary="今日超期客户摘要(首屏提醒用)",
)
async def overdue_summary(user: CurrentUser, db: DBSession) -> OverdueSummary:
    return await customer_service.get_overdue_summary(db, user)


@router.get(
    "/{customer_id}",
    response_model=CustomerDetail,
    summary="客户 360 详情",
)
async def get_customer(
    customer_id: UUID,
    user: CurrentUser,
    db: DBSession,
) -> CustomerDetail:
    detail = await customer_service.get_customer_detail(db, user, customer_id)
    if detail is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Customer not found or not accessible",
        )
    return detail
