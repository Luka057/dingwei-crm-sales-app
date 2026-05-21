"""
async engine + async_sessionmaker(单例,模块级)。

引擎在模块加载时创建一次。测试用 fixture 覆盖 AsyncSessionLocal 即可。
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()


# ── Async Engine ────────────────────────────────────────────────


def _make_engine() -> AsyncEngine:
    """创建 async engine。pool 配置按 50 并发上限定."""
    return create_async_engine(
        _settings.database_url,
        echo=_settings.db_echo,
        # SQL Server 连接池:基础 5 + 溢出 15 = 峰值 20,够 50 同时在线
        pool_size=5,
        max_overflow=15,
        pool_pre_ping=True,   # 自动重连断连接
        pool_recycle=1800,    # 30 分钟 recycle,SQL Server 默认 idle 超时 30+ 分钟
        future=True,
    )


engine: AsyncEngine = _make_engine()


# ── Async Session ───────────────────────────────────────────────

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # commit 后 ORM 对象仍可读字段,FastAPI 响应需要
    autoflush=False,
    autocommit=False,
)


__all__ = ["AsyncSessionLocal", "engine"]
