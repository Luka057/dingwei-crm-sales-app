"""
main.py — FastAPI 服务入口。

路由:
  GET  /health          —— 健康检查（模式、索引大小）
  POST /sample-search   —— 三路融合图片检索
  GET  /images/{file}   —— 静态文件服务（样本图片）

启动:
  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.model import Embedder, MockEmbedder, build_embedder
from app.schemas import SampleSearchRequest, SampleSearchResponse
from app.search import run_search
from app.vector_store import FaissStore, VectorStore

# 配置日志格式（显示时间、级别、模块名）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# 应用状态（生命周期内共享的对象）
# ─────────────────────────────────────────────────────────────────

# 使用字典而非全局变量，方便在测试中替换
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理。
    startup: 初始化嵌入器 + 加载向量索引
    shutdown: 清理资源
    """
    settings = get_settings()

    # ── 初始化嵌入器 ─────────────────────────────────────────────
    embedder = build_embedder(settings)
    _state["embedder"] = embedder

    # ── 加载向量索引 ─────────────────────────────────────────────
    index_faiss = os.path.join(settings.index_path, "index.faiss")
    index_meta = os.path.join(settings.index_path, "metadata.json")

    if os.path.exists(index_faiss) and os.path.exists(index_meta):
        store = FaissStore.load(settings.index_path)
        logger.info("[startup] 向量索引已加载，共 %d 条", store.count)
    else:
        # 索引不存在时创建空索引，服务仍可启动（/health 会显示 indexed=0）
        logger.warning(
            "[startup] 未找到向量索引（%s），将使用空索引。"
            "请先运行: python index_samples.py --manifest samples.csv --images ./corpus --out ./index",
            settings.index_path,
        )
        store = FaissStore(embed_dim=settings.embed_dim)

    _state["store"] = store

    # ── 挂载静态文件（图片目录）────────────────────────────────────
    images_dir = settings.images_dir
    if os.path.isdir(images_dir):
        app.mount("/images", StaticFiles(directory=images_dir), name="images")
        logger.info("[startup] 已挂载图片目录: %s → /images", images_dir)
    else:
        logger.warning(
            "[startup] 图片目录不存在: %s。/images 路由不可用。"
            "请先运行 make_demo_corpus.py 或指定正确的 VISION_IMAGES_DIR",
            images_dir,
        )

    logger.info("[startup] vision-service 就绪")
    yield

    # ── 关闭时清理 ───────────────────────────────────────────────
    _state.clear()
    logger.info("[shutdown] vision-service 已关闭")


# ─────────────────────────────────────────────────────────────────
# FastAPI 应用实例
# ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="鼎伟 CRM — AI 找板 Vision Service",
    description=(
        "SigLIP2 图文嵌入 + FAISS 向量检索的样本推荐服务。\n\n"
        "默认运行在 mock 模式（VISION_USE_MOCK=true），"
        "无需 torch/transformers 即可本地验证管道。"
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────────
# 依赖注入
# ─────────────────────────────────────────────────────────────────

def get_embedder() -> Embedder:
    """从应用状态中取出嵌入器实例。"""
    return _state["embedder"]


def get_store() -> VectorStore:
    """从应用状态中取出向量存储实例。"""
    return _state["store"]


# ─────────────────────────────────────────────────────────────────
# 中间件：Bearer Token 鉴权（可选）
# ─────────────────────────────────────────────────────────────────

async def _check_auth(request: Request, settings: Settings) -> None:
    """
    若配置了 service_token，则要求请求头携带:
      Authorization: Bearer <token>
    """
    token = settings.service_token
    if not token:
        return  # 未配置 → 不鉴权
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization: Bearer <token> 请求头",
        )
    if auth[len("Bearer "):].strip() != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token 无效",
        )


# ─────────────────────────────────────────────────────────────────
# 路由
# ─────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    summary="健康检查",
    response_description="服务状态、运行模式、索引大小",
)
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    健康检查端点，用于:
      - 确认服务已启动
      - 查看当前运行模式（mock / siglip）
      - 查看向量索引中的样本数量
    """
    embedder = get_embedder()
    store = get_store()

    # 判断当前模式
    mode = "mock" if isinstance(embedder, MockEmbedder) else "siglip"

    return {
        "ok": True,
        "mode": mode,
        "indexed": store.count,
        "embed_dim": settings.embed_dim,
        "vector_store": settings.vector_store,
    }


@app.post(
    "/sample-search",
    response_model=SampleSearchResponse,
    summary="样本相似图检索",
    response_description="按融合分数降序排列的样本列表",
)
async def sample_search(
    req: SampleSearchRequest,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
):
    """
    三路融合样本检索:
      - 图片向量（视觉外观）
      - 文本向量（文字描述）
      - 工艺参数匹配（宽度/张力/类型）

    请求体示例:
    ```json
    {
      "image_base64": "<base64>",
      "description": "提花织带 黑色",
      "filters": {"ribbon_type": "提花织带"},
      "top_k": 5
    }
    ```
    """
    # 鉴权检查
    await _check_auth(request, settings)

    embedder = get_embedder()
    store = get_store()

    result = await run_search(req, embedder, store, settings)
    return result
