"""
search.py — 核心检索逻辑。

流程:
  1. 解码查询图片（base64 或 URL）→ PIL.Image
  2. 嵌入：图片向量 q_img + 文本向量 q_txt
  3. ANN 检索：用图片向量（或文本向量）从 FAISS 拉取候选
  4. 重排：对每个候选计算三路分数，融合排序
  5. 构建响应

文本专搜（无图片）: 用 q_txt 做 ANN，image_sim 设为 0。
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Optional

import httpx
import numpy as np
from PIL import Image

from app.config import Settings
from app.fusion import fuse, process_similarity
from app.model import Embedder
from app.schemas import Match, SampleSearchRequest, SampleSearchResponse, ScoreComponents
from app.vector_store import VectorStore

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# 工具函数：图片解码
# ─────────────────────────────────────────────────────────────────

def _decode_base64_image(b64: str) -> Image.Image:
    """
    将 base64 字符串解码为 PIL.Image。
    自动去除 data:image/xxx;base64, 前缀。
    """
    # 去掉 data URI 前缀（如 "data:image/png;base64,"）
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    # 去掉可能的空白字符
    b64 = b64.strip()
    raw = base64.b64decode(b64)
    return Image.open(io.BytesIO(raw)).convert("RGB")


async def _fetch_url_image(url: str) -> Image.Image:
    """
    异步 HTTP GET 下载图片 URL，返回 PIL.Image。
    超时 10 秒。
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content)).convert("RGB")


# ─────────────────────────────────────────────────────────────────
# 工具函数：余弦相似度
# ─────────────────────────────────────────────────────────────────

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    """
    计算两个向量的余弦相似度。
    若任一向量为零则返回 0.0。
    假设输入已 L2 归一化，则直接点积即可；
    此函数做了保险归一化以应对未归一化的输入。
    """
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return float(np.dot(a / na, b / nb))


# ─────────────────────────────────────────────────────────────────
# 主检索函数
# ─────────────────────────────────────────────────────────────────

async def run_search(
    req: SampleSearchRequest,
    embedder: Embedder,
    store: VectorStore,
    settings: Settings,
) -> SampleSearchResponse:
    """
    执行完整的"图片 + 文字 + 工艺"三路融合检索。

    参数:
      req      —— 解析好的请求体
      embedder —— 嵌入器（MockEmbedder 或 SiglipEmbedder）
      store    —— 向量存储（FaissStore）
      settings —— 服务配置

    返回:
      SampleSearchResponse，包含 top_k 个 Match
    """
    # ── Step 1: 解码查询图片 ─────────────────────────────────────
    img: Image.Image | None = None

    if req.image_base64:
        try:
            img = _decode_base64_image(req.image_base64)
        except Exception as exc:
            logger.warning("[search] image_base64 解码失败: %s", exc)

    if img is None and req.image_url:
        try:
            img = await _fetch_url_image(req.image_url)
        except Exception as exc:
            logger.warning("[search] image_url 获取失败: %s", exc)

    # ── Step 2: 计算查询向量 ──────────────────────────────────────
    # q_img: 图片查询向量（无图片时为 None）
    # q_txt: 文本查询向量（无描述时仍然计算，只是文本为空串）
    q_img: Optional[np.ndarray] = None
    if img is not None:
        q_img = embedder.embed_image(img)

    q_txt: np.ndarray = embedder.embed_text(req.description)

    # ── Step 3: ANN 检索 —— 拉取候选 ────────────────────────────
    # 优先用图片向量；无图片时退回文本向量（纯文本搜索）
    ann_vector = q_img if q_img is not None else q_txt

    candidates = store.search(ann_vector, k=settings.top_k_ann)
    # candidates: [(faiss_cosine_score, payload), ...]
    # payload 结构见 index_samples.py，字段: sample_no, external_id,
    #   image_file, text_emb, metadata

    if not candidates:
        logger.info("[search] 索引为空或无结果，返回空列表")
        return SampleSearchResponse(matches=[])

    # ── Step 4: 重排 —— 计算三路分数并融合 ───────────────────────
    ranked: list[tuple[float, ScoreComponents, dict]] = []

    filters_dict = req.filters.model_dump()

    for ann_score, payload in candidates:
        # 图片相似度：来自 FAISS 内积（L2归一化后 = 余弦）
        # 无图片时 image_sim = 0（ANN 用的是文本向量，ann_score 算的是文本余弦）
        if q_img is not None:
            image_sim = float(ann_score)
        else:
            image_sim = 0.0

        # 文本相似度：查询文本向量 vs 样本预计算文本嵌入
        payload_text_emb = payload.get("text_emb")
        if payload_text_emb is not None and q_txt is not None:
            text_sim = _cosine(q_txt, np.array(payload_text_emb, dtype=np.float32))
        else:
            text_sim = 0.0

        # 工艺匹配度：过滤字段命中率
        sample_metadata = payload.get("metadata", {})
        proc_sim = process_similarity(filters_dict, sample_metadata)

        # 融合分数
        score = fuse(image_sim, text_sim, proc_sim, settings.fusion_weights)

        components = ScoreComponents(
            image=round(image_sim, 4),
            text=round(text_sim, 4),
            process=round(proc_sim, 4),
        )
        ranked.append((score, components, payload))

    # 按融合分数降序排列
    ranked.sort(key=lambda x: x[0], reverse=True)

    # 取 top_k
    ranked = ranked[: req.top_k]

    # ── Step 5: 构建响应 ─────────────────────────────────────────
    matches: list[Match] = []
    for score, components, payload in ranked:
        image_file = payload.get("image_file", "")
        matches.append(
            Match(
                external_id=payload.get("external_id"),
                sample_no=payload.get("sample_no", ""),
                score=round(score, 4),
                score_components=components,
                image_url=f"/images/{image_file}",
                metadata=payload.get("metadata", {}),
            )
        )

    logger.info(
        "[search] 检索完成 — candidates=%d, returned=%d, top_score=%.4f",
        len(candidates),
        len(matches),
        matches[0].score if matches else 0.0,
    )

    return SampleSearchResponse(matches=matches)
