"""
Auth router.

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /auth/login: 公开,所有角色

约束:
- bcrypt 密码校验(passlib)
- 签发 JWT(HS256, 7 天过期 - 试点期)
- 异常统一 401(不暴露原因)
"""

from fastapi import APIRouter, HTTPException, status

from app.core.deps import DBSession
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import InvalidCredentialsError, authenticate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="登录(公开)",
    responses={401: {"description": "用户名或密码错误"}},
)
async def login(payload: LoginRequest, db: DBSession) -> LoginResponse:
    try:
        return await authenticate(db, payload.username, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
