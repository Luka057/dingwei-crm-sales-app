"""
AI router — /ai/chat 仍为 stub;/ai/board-search 已接真视觉服务(瘦代理)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /ai/chat           Sales/Manager,1A stub
- POST /ai/board-search   Sales/Manager,调 vision-service /sample-search

§6.1-6.4 AI 4 个真痛点:board-search Phase 2 已接视觉服务;其余 stub,Phase 1B 接 DeepSeek。
"""

from fastapi import APIRouter, HTTPException

from app.core.deps import CurrentUser, DBSession
from app.schemas.ai import (
    AiBoardSearchMatch,
    AiBoardSearchRequest,
    AiBoardSearchResponse,
    AiChatRequest,
    AiChatResponse,
)
from app.services import upload_service
from app.services import vision_service
from app.services.vision_service import VisionServiceError

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/chat",
    response_model=AiChatResponse,
    summary="AI 聊天(1A stub)",
)
async def ai_chat(
    payload: AiChatRequest, user: CurrentUser, db: DBSession
) -> AiChatResponse:
    """1A stub 固定回话;Phase 1B 接 DeepSeek Function Calling
    (查 customer/visit/order 等结构化数据)。"""
    return AiChatResponse(
        reply=(
            f"(stub) 收到你的问题:{payload.message[:50]}...\n"
            "AI 客户问答 Phase 1B 真接入 DeepSeek 后启用,详见 §6.3。"
        ),
        cards=[],
    )


@router.post(
    "/board-search",
    response_model=AiBoardSearchResponse,
    summary="AI 找板(调视觉服务 /sample-search,瘦代理)",
)
async def ai_board_search(
    payload: AiBoardSearchRequest, user: CurrentUser, db: DBSession
) -> AiBoardSearchResponse:
    """调公司视觉服务(SigLIP2 + 向量索引)做样板搜索。

    流程:
      1. 从 image_ids 中解析出第一张可访问的图片字节(owner/manager JWT 鉴权复用)
      2. 拼接 description 文本描述
      3. 转发 → vision-service /sample-search
      4. 映射返回结果到 AiBoardSearchMatch
    若视觉服务不可用,返回 503(不崩溃)。
    """

    # ── 1. 解析图片 ─────────────────────────────────────────────
    image_bytes: bytes | None = None
    for image_id in payload.image_ids:
        # get_visit_photo_path 内置 owner/manager 鉴权,返回 (Path, mime)|None
        result = await upload_service.get_visit_photo_path(db, user, image_id)
        if result is not None:
            path, _mime = result
            try:
                image_bytes = path.read_bytes()
                break  # 只取第一张可解析的图片
            except OSError:
                continue  # 文件不可读(竞态删除/卷未挂)→ 当作不存在,继续找下一张

    # ── 2. 拼接文本描述 ──────────────────────────────────────────
    # 把非空的场景/需求/规格字段拼成一段描述,空字段跳过
    parts = [
        payload.customer_scene,
        payload.requirements,
        f"{payload.width}" if payload.width else None,
        f"开力度{payload.tension}" if payload.tension else None,
        payload.ribbon_type,
    ]
    description = " ".join(p for p in parts if p)

    # ── 3. 构建过滤条件 ──────────────────────────────────────────
    filters: dict[str, str | None] = {
        "width": payload.width or None,
        "tension": payload.tension or None,
        "ribbon_type": payload.ribbon_type or None,
    }

    # ── 4. 调视觉服务 ────────────────────────────────────────────
    try:
        matches_raw = await vision_service.search_samples(image_bytes, description, filters)
    except VisionServiceError as exc:
        raise HTTPException(503, "AI 找板服务暂时不可用，请稍后再试") from exc

    # ── 5. 映射结果到 schema ─────────────────────────────────────
    matches: list[AiBoardSearchMatch] = []
    for m in matches_raw:
        meta = m.get("metadata", {})
        sc = m.get("score_components")

        # 从 score_components 合成可读的 reason(若视觉服务有返回)
        reason: str | None = None
        if sc:
            reason = (
                f"图片相似 {round(sc.get('image', 0) * 100)}%"
                f" · 文本 {round(sc.get('text', 0) * 100)}%"
                f" · 工艺 {round(sc.get('process', 0) * 100)}%"
            )

        matches.append(
            AiBoardSearchMatch(
                sample_no=m.get("sample_no", ""),
                score=m.get("score", 0.0),
                reason=reason,
                image_url=m.get("image_url"),
                external_id=m.get("external_id"),
                width=meta.get("width"),
                tension=meta.get("tension"),
                ribbon_type=meta.get("ribbon_type"),
                color=meta.get("color"),
                status=meta.get("status"),
            )
        )

    return AiBoardSearchResponse(matches=matches)
