"""
Auth service — 登录鉴权。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /auth/login: 公开

业务规则:
- 只 status='active' 用户能登录
- role='boss' 账号在本应用拒绝登录(老板用老板端)— §3.3 不存在 Boss
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import LoginResponse, UserInfo


class InvalidCredentialsError(Exception):
    """统一身份错误,调用方转 401。"""


async def authenticate(
    db: AsyncSession,
    username: str,
    password: str,
) -> LoginResponse:
    """
    校验用户名密码,签发 JWT。

    抛 InvalidCredentialsError 时统一返 401 不区分原因(防探测):
      - 用户不存在
      - 密码错
      - 账号 disabled/resigned
      - 账号是 boss 角色(本应用不允许)
    """
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None:
        raise InvalidCredentialsError("user not found")

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("bad password")

    if user.status != UserStatus.ACTIVE:
        raise InvalidCredentialsError(f"user status={user.status.value}")

    if user.role == UserRole.BOSS:
        raise InvalidCredentialsError("boss role not allowed in sales app")

    token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "role": user.role.value,
            "name": user.name,
        },
    )

    return LoginResponse(
        token=token,
        user=UserInfo(
            id=user.id,
            username=user.username,
            name=user.name,
            role=user.role,
            manager_id=user.manager_id,
        ),
    )
