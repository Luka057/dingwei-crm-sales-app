"""
AI router(1A 全 stub,接口契约固定)。

角色矩阵参考:docs/需求文档-v2.md §3.5.2
- POST /ai/chat           Sales/Manager,1A stub
- POST /ai/board-search   Sales/Manager,1A stub(Q6 决议:返 3 条拟真 mock)

§6.1-6.4 AI 4 个真痛点全 stub,Phase 1B 接 DeepSeek + Phase 2 接视觉模型。
"""

from fastapi import APIRouter

from app.core.deps import CurrentUser, DBSession
from app.schemas.ai import (
    AiBoardSearchMatch,
    AiBoardSearchRequest,
    AiBoardSearchResponse,
    AiChatRequest,
    AiChatResponse,
)

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
    summary="AI 找板(1A stub 返 3 条拟真 mock,Q6 决议)",
)
async def ai_board_search(
    payload: AiBoardSearchRequest, user: CurrentUser, db: DBSession
) -> AiBoardSearchResponse:
    """Q6 决议:1A 完整 UI + stub 返 mock(3 条拟真样板),试点反馈有意义。

    Phase 2 实施(§6.4):SigLIP2+DINOv2 双路 + Milvus + LoRA 微调。
    """
    return AiBoardSearchResponse(
        matches=[
            AiBoardSearchMatch(
                sample_no="HY-20-BK-soft",
                score=0.92,
                reason="宽度匹配,颜色相近,关联宏远历史样板",
            ),
            AiBoardSearchMatch(
                sample_no="JH-18-DG-rib",
                score=0.85,
                reason="工艺参数接近,推荐参考",
            ),
            AiBoardSearchMatch(
                sample_no="HJ-22-NV-twill",
                score=0.78,
                reason="织带类型同类,可作备选",
            ),
        ]
    )
