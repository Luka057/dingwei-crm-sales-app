"""客户转移 DTO — 对齐 §3.4 + §3.5.6 + §3.5.5 Q3(1A 不撤销)。"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.customer_transfer import TransferFlow, TransferStatus
from app.schemas.common import APIModel


class CustomerTransferCreate(APIModel):
    """POST /customer-transfers 请求体。

    flow 字段决定行为:
      - manager_direct:Manager 调,立即生效(status=executed)
      - sales_request:Sales 调,进入 pending 等主管审批

    后端按 current_user.role 校验 flow 合法性。
    """

    customer_id: UUID
    to_user_id: UUID
    flow: TransferFlow
    reason: str | None = Field(default=None, max_length=500)


class CustomerTransferOut(APIModel):
    """详情 / 列表项共用。"""

    id: UUID
    customer_id: UUID
    customer_name: str | None = None  # join customer.name
    from_user_id: UUID
    from_user_name: str | None = None
    to_user_id: UUID
    to_user_name: str | None = None
    initiated_by_user_id: UUID
    flow: TransferFlow
    status: TransferStatus
    reason: str | None = None
    requested_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by_user_id: UUID | None = None
