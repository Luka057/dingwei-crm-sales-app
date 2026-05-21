"""
SQLAlchemy 基础设施 — DeclarativeBase + 类型别名。

所有 ORM 模型继承 Base。Alembic env.py 通过 Base.metadata 自动发现表结构。

SQL Server 适配点(详见 docs/技术栈选型-v2.md §4):
- 主键:UNIQUEIDENTIFIER (Uuid as_uuid=True),Python 侧 default=uuid.uuid4
- 时间:DATETIME2(7) (TIMESTAMP with sysutcdatetime)
- ENUM:VARCHAR + CHECK (native_enum=False)
- 布尔:BIT
- 外键 SetNull 仅用于 Plan.customer_id;其他 RESTRICT(避免多路 cascade 报错)
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的根。

    不用 MappedAsDataclass(避免 __init__ 限制带来的灵活度损失)。
    需要 dataclass 风格的 schema 时,Pydantic 在 schemas/ 层做。
    """


# ── 通用列类型别名(类型注解 + 默认值) ─────────────────────────


PKUuid = Annotated[
    UUID,
    mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
        # SQL Server 端默认 NEWID(),但 Python 侧 default=uuid4 已足够,
        # 不依赖 server_default 避免 returning 子句方言差异。
    ),
]


FKUuid = Annotated[
    UUID,
    mapped_column(Uuid(as_uuid=True)),
]


OptFKUuid = Annotated[
    UUID | None,
    mapped_column(Uuid(as_uuid=True), nullable=True),
]


CreatedAt = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=False),  # SQL Server DATETIME2,UTC,不带时区
        server_default=func.sysutcdatetime(),
        nullable=False,
    ),
]


UpdatedAt = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=False),
        server_default=func.sysutcdatetime(),
        onupdate=func.sysutcdatetime(),
        nullable=False,
    ),
]


# 集成预留字段(user / customer / sample 用)
# 见 docs/需求文档-v2.md §5.3 共享 ID
ExternalId = Annotated[str | None, mapped_column(String(64), nullable=True)]
SourceSystem = Annotated[str | None, mapped_column(String(32), nullable=True)]
SyncedAt = Annotated[datetime | None, mapped_column(DateTime(timezone=False), nullable=True)]


__all__ = [
    "Base",
    "CreatedAt",
    "ExternalId",
    "FKUuid",
    "OptFKUuid",
    "PKUuid",
    "SourceSystem",
    "SyncedAt",
    "UpdatedAt",
]
