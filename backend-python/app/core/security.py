"""
鉴权工具 — bcrypt 密码哈希 + JWT 签发/解码。

参考:`../../docs/需求文档-v2.md §7 安全`。
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# bcrypt 上下文 — passlib + bcrypt 4.x 兼容
# (deprecated="auto" 会在未来 bcrypt 升级时自动 re-hash 旧密码)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── 密码 ────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """bcrypt 哈希密码。"""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码;hash 不对返回 False,不抛错。"""
    try:
        return _pwd_context.verify(plain, hashed)
    except ValueError:
        # 异常 hash 字符串
        return False


# ── JWT ─────────────────────────────────────────────────────────


def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    签发 JWT。

    :param subject: 通常是 user.id (str)
    :param extra_claims: role / name 等附加 claim
    :param expires_delta: 默认走 settings.jwt_access_token_expire_minutes
    """
    settings = get_settings()
    now = datetime.now(UTC)
    exp = now + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": exp,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    解码并校验 JWT。

    :raises JWTError: 签名失败 / 过期 / 格式错。调用方应转 401 HTTPException。
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )


__all__ = [
    "JWTError",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
