"""
Customers router(含 overdue-summary)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- GET /customers              Sales/Manager 看自己的(owner_id 过滤)
- GET /customers/{id}         Sales/Manager owner 校验
- GET /customers/overdue-summary  Sales/Manager 自己的超期客户

实施时:service 层 SELECT 必带 WHERE owner_id = :uid(§3.5.3)。
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DBSession
from app.schemas.customer import CustomerDetail, CustomerListItem, OverdueSummary

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
    """筛选项:keyword / level / overdue。

    §3.5.3 硬规则:WHERE owner_id = current_user.id
    """
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.2 — customers module)",
    )


@router.get(
    "/overdue-summary",
    response_model=OverdueSummary,
    summary="今日超期客户摘要(首屏提醒用)",
)
async def overdue_summary(user: CurrentUser, db: DBSession) -> OverdueSummary:
    """运行时按 A14d/B30d/C60d 计算,返回数字 + 列表前 5(§5.2)。"""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.2 — overdue module)",
    )


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
    """含基本资料 + KPI + 近 N 条 visit_record(§4.1)。"""
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        "Not implemented (Phase 1A.2 — customers module)",
    )
