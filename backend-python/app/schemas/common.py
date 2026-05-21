"""共享 schema 工具。"""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIModel(BaseModel):
    """所有响应 DTO 的基类。

    ConfigDict:
    - from_attributes=True:支持 SQLAlchemy ORM 对象直接转 DTO
    - populate_by_name=True:接受 alias 和 field name 都行
    - str_strip_whitespace=True:字符串自动 strip
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class Paginated(APIModel, Generic[T]):
    """分页响应。"""

    items: list[T]
    total: int
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=100)


class ErrorDetail(APIModel):
    """统一错误响应 schema。FastAPI 默认 HTTPException 也走类似形态。"""

    detail: str
    code: str | None = None
