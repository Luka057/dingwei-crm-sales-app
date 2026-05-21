"""
FastAPI 依赖注入 — DB session、当前用户、角色校验。

引用:`../../docs/需求文档-v2.md §3.5.1 设计原则`。

权限边界规则:
- get_current_user: 所有业务端点必须声明,public 端点(/health, /auth/login)不声明
- require_manager: manager-only 端点(transfer approve/reject, weekly-report reopen,
  /manager/*, customer-transfer 下属待审视图)必须声明

实施 grep 核对清单(见 §3.5.3 数据可见性硬规则):
service 层方法首参 `user: AuthUser`,SELECT 必带 owner_id/salesperson_id 过滤。
"""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import JWTError, decode_access_token
from app.db.session import AsyncSessionLocal

# OAuth2 Bearer scheme — 前端把 JWT 放在 Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ── DB Session ──────────────────────────────────────────────────


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    Per-request async session,自动 close。

    用法:
        async def endpoint(db: Annotated[AsyncSession, Depends(get_db)]): ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        # commit 由 service / endpoint 显式控制,不在依赖里 auto-commit


DBSession = Annotated[AsyncSession, Depends(get_db)]


# ── 当前用户 ─────────────────────────────────────────────────────


class AuthUser:
    """
    解析自 JWT 的当前用户上下文。

    业务层只持有这个轻量对象,不持有 ORM User 实例(避免 session 跨依赖泄漏)。
    需要更多字段时去 DB 查。
    """

    __slots__ = ("id", "role", "name", "manager_id")

    def __init__(
        self,
        user_id: str,
        role: str,
        name: str,
        manager_id: str | None = None,
    ) -> None:
        self.id = user_id
        self.role = role
        self.name = name
        self.manager_id = manager_id

    @property
    def is_manager(self) -> bool:
        return self.role == "manager"

    @property
    def is_sales(self) -> bool:
        return self.role == "sales"


_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    db: DBSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> AuthUser:
    """
    所有业务端点用这个依赖。public 端点(/health, /auth/login)不声明。

    流程:
      1. 解 JWT → 拿到 user_id (sub)
      2. DB 查 User → 验证存在且 status='active'
      3. 返回 AuthUser(id/role/name/manager_id)

    任何一步失败统一 401(不暴露具体原因)。
    """
    # 延迟导入,避免循环依赖(models 引用 db,deps 引用 models)
    from sqlalchemy import select

    from app.models.user import User, UserStatus

    if token is None:
        raise _CREDENTIALS_EXCEPTION

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise _CREDENTIALS_EXCEPTION
    except JWTError as exc:
        raise _CREDENTIALS_EXCEPTION from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or user.status != UserStatus.ACTIVE:
        raise _CREDENTIALS_EXCEPTION

    return AuthUser(
        user_id=str(user.id),
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        name=user.name,
        manager_id=str(user.manager_id) if user.manager_id else None,
    )


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]


# ── 角色校验 ─────────────────────────────────────────────────────


async def require_manager(user: CurrentUser) -> AuthUser:
    """
    Manager-only 端点用这个依赖。

    覆盖范围(§3.5.2 端点矩阵 manager-only):
      - POST /weekly-reports/{id}/reopen
      - PUT /customer-transfers/{id}/approve
      - PUT /customer-transfers/{id}/reject
      - GET /manager/team-summary
      - GET /manager/subordinates/{userId}/visits
    """
    if not user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager role required",
        )
    return user


ManagerUser = Annotated[AuthUser, Depends(require_manager)]


__all__ = [
    "AuthUser",
    "CurrentUser",
    "DBSession",
    "ManagerUser",
    "get_current_user",
    "get_db",
    "require_manager",
]
