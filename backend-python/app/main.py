"""
FastAPI 入口。

启动方式:
  uvicorn app.main:app --reload --port 3000

OpenAPI 文档:http://localhost:3000/docs
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """启动 / 关闭钩子。

    1A:仅日志 + engine pool 已自动管理。
    Phase 1B:可在此添 Redis 连接池 / DeepSeek client 初始化等。
    """
    # 启动时校验 settings
    _ = get_settings()
    yield
    # shutdown:目前无操作


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="鼎伟 CRM 业务人员端 - 后端",
        description=(
            "Phase 1A — Python + FastAPI + SQL Server。\n\n"
            "**角色矩阵**:见 `docs/需求文档-v2.md §3.5`。\n"
            "**端点 × 角色**:见 §3.5.2。\n"
        ),
        version="0.1.0",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        lifespan=lifespan,
    )

    # CORS — 前端 vite dev 5173 / nginx 8080
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # /api/v1 路由
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
