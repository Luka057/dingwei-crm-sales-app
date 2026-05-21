"""
鉴权工具 — bcrypt 密码哈希 + JWT 签发/解码。

参考:`../../docs/需求文档-v2.md §7 安全`。

设计决策(2026-05-21 实施时调整):
- 直接用 `bcrypt` 库,**不走 passlib**。原因:
  passlib 1.7.4(2024-至今最后版)的后端探测 routine
  在初始化 CryptContext 时调用 `bcrypt.hashpw(>72_byte_secret, ...)`,
  bcrypt 4.x 不再 silent-truncate,会 raise ValueError → CryptContext
  初始化崩。短期解决方案是 pin bcrypt<4.1,但与时俱进的做法是
  跳过 passlib 直接调 bcrypt 4.x。bcrypt 库本身够稳定,
  passlib 的 multi-scheme 抽象在本项目用不到(只 bcrypt)。

bcrypt 限制:secret 最长 72 字节,UTF-8 编码后超出需手动截断
(我们对 password 做 [:72] 截断,与 passlib 1.7.x 的旧默认行为一致)。
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

# 默认轮数 12(2^12 = 4096 次,~250ms/hash on M1,适合用户登录场景)
_BCRYPT_ROUNDS = 12


# ── 密码 ────────────────────────────────────────────────────────


def _secret_bytes(plain: str) -> bytes:
    """UTF-8 编码 + 截断到 72 字节(bcrypt 上限)。"""
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    """bcrypt 哈希密码,返回 UTF-8 字符串供存 DB。"""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    return bcrypt.hashpw(_secret_bytes(plain), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验密码;hash 字符串无效或不匹配返 False,不抛错。"""
    try:
        return bcrypt.checkpw(_secret_bytes(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # hash 字符串格式错(非 bcrypt 字符串)
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
