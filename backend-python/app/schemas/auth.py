"""Auth 端点 DTO — 对齐 docs/接口文档.md §1。"""

from uuid import UUID

from pydantic import Field

from app.models.user import UserRole
from app.schemas.common import APIModel


class LoginRequest(APIModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class UserInfo(APIModel):
    """登录响应里的 user 字段(精简版)。

    Manager 调 /customers 时本接口不增,但客户端可凭 role 字段决定是否显示
    日历 tab 顶部「团队概览」卡片(Q1 决议)。
    """

    id: UUID
    username: str
    name: str
    role: UserRole
    manager_id: UUID | None = None


class LoginResponse(APIModel):
    token: str
    user: UserInfo
