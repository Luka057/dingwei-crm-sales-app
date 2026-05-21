"""AI 端点 DTO — 1A 全 stub,接口契约固定(§6 + §3.5.5 Q6 决议)。

Q6 决议:AI 找板 sheet 1A 完整 UI + stub 返 mock(3 条拟真样板)。
"""

from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import APIModel


# ── /ai/chat ────────────────────────────────────────────────────


class AiChatRequest(APIModel):
    """1A 简化版,只接收 message。

    Phase 1B 真接入 DeepSeek Function Calling 时扩展:
      - conversation_id(多轮)
      - tool_choice(function calling)
    """

    message: str = Field(min_length=1, max_length=2000)


class AiChatCard(APIModel):
    """AI 回复里可能嵌入的卡片(客户/拜访/订单卡片预览)。"""

    type: str
    data: dict[str, Any]


class AiChatResponse(APIModel):
    reply: str
    cards: list[AiChatCard] = Field(default_factory=list)


# ── /ai/board-search(找板) ────────────────────────────────────


class AiBoardSearchRequest(APIModel):
    """对应原 docs/接口文档.md §11 + §6.4。

    image_ids:前端先调 /uploads/visit-photo 拿 id,再带在这里。
    """

    customer_scene: str = Field(min_length=1, max_length=200)
    image_ids: list[UUID] = Field(default_factory=list, max_length=5)
    width: str | None = None
    tension: str | None = None
    ribbon_type: str | None = None
    requirements: str | None = None


class AiBoardSearchMatch(APIModel):
    sample_no: str
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class AiBoardSearchResponse(APIModel):
    """1A stub 返回 3 条拟真 mock(Q6 决议)。"""

    matches: list[AiBoardSearchMatch] = Field(default_factory=list)
