"""Alembic 环境 — async engine 适配。

兼容性:
- 在线模式:用 app 的 async engine 跑迁移(`alembic upgrade head` 时)
- 离线模式:生成 SQL 脚本(`alembic upgrade head --sql > out.sql`)
- 由于 SQL Server + aioodbc 无完美 sync fallback,offline 模式用 pyodbc URL
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── 路径 / 配置 ─────────────────────────────────────────────────

# 让 alembic 子进程能 import app.*
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# noinspection PyUnresolvedReferences
from app.core.config import get_settings  # noqa: E402
from app.models import Base  # noqa: E402  # 触发所有 model 注册

# 注入运行时 URL
config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Offline ─────────────────────────────────────────────────────


def run_migrations_offline() -> None:
    """offline 模式 — 生成 SQL 不连 DB。"""
    # offline 用同步 pyodbc URL(aioodbc 不支持 offline)
    context.configure(
        url=settings.database_url_sync,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online (async) ──────────────────────────────────────────────


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ── Entrypoint ──────────────────────────────────────────────────


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
