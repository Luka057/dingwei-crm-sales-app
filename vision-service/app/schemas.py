"""
schemas.py — API 请求/响应的 Pydantic 数据模型。

这些模型同时服务两个目的:
  1. 请求验证 — FastAPI 在收到请求时自动用这些类型校验 JSON
  2. 文档生成 — FastAPI 用这些模型自动生成 OpenAPI / Swagger 文档

字段说明见各类的 docstring。
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────
# 请求模型
# ─────────────────────────────────────────────────────────────────

class Filters(BaseModel):
    """
    工艺过滤条件（全部可选）。
    非 None 的字段会参与 process_similarity() 的匹配计算。

    字段:
      width       —— 织带宽度，如 "20mm"、"25mm"
      tension     —— 张力 / 弹力等级，如 "soft"、"medium"、"hard"
      ribbon_type —— 织带类型，如 "提花织带"、"平纹织带"
    """
    width: Optional[str] = None
    tension: Optional[str] = None
    ribbon_type: Optional[str] = None


class SampleSearchRequest(BaseModel):
    """
    /sample-search 接口的请求体。

    至少提供 image_base64、image_url、description 三者之一；
    若三者都缺失，服务会以零向量执行纯随机检索（无实际意义）。

    字段:
      image_base64  —— base64 编码的图片（可带 data:image/png;base64, 前缀）
      image_url     —— 可公开访问的图片 URL（优先级低于 image_base64）
      description   —— 文字描述，如 "黑色提花织带，宽20mm"
      filters       —— 工艺过滤条件（不传则默认全部为 None）
      top_k         —— 返回的最大结果数（默认 10，最大受 top_k_ann 限制）
    """
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64 编码的查询图片，可带 data: URI 前缀",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="可公开访问的查询图片 URL",
    )
    description: str = Field(
        default="",
        description="文字描述，用于文本嵌入检索",
    )
    filters: Filters = Field(
        default_factory=Filters,
        description="工艺参数过滤条件",
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=200,
        description="期望返回的结果数量",
    )


# ─────────────────────────────────────────────────────────────────
# 响应模型
# ─────────────────────────────────────────────────────────────────

class ScoreComponents(BaseModel):
    """
    融合分数的三路分解，便于调试和权重调优。

    字段:
      image   —— 图片余弦相似度（来自 FAISS 检索）
      text    —— 文本余弦相似度（查询描述 vs 样本文本嵌入）
      process —— 工艺匹配率（过滤字段命中比例）
    """
    image: float = Field(description="图片余弦相似度 [-1, 1]")
    text: float = Field(description="文本余弦相似度 [-1, 1]")
    process: float = Field(description="工艺匹配率 [0, 1]")


class Match(BaseModel):
    """
    单条检索结果。

    字段:
      external_id      —— 对接 ERP 系统的外部 ID（可为 None）
      sample_no        —— 样本编号，如 "HY-20-BK-soft"
      score            —— 最终融合分数 [0, 1]，越高越相似
      score_components —— 三路分数明细，便于排查和调优
      image_url        —— 样本图片的相对 URL（如 /images/sample_001.png）
      metadata         —— 样本的全部元数据字段（宽度、张力、颜色等）
    """
    external_id: Optional[str] = Field(default=None, description="ERP 外部 ID")
    sample_no: str = Field(description="样本编号")
    score: float = Field(description="融合分数 [0, 1]")
    score_components: ScoreComponents = Field(description="三路分数明细")
    image_url: str = Field(description="样本图片相对 URL")
    metadata: dict = Field(description="样本完整元数据")


class SampleSearchResponse(BaseModel):
    """
    /sample-search 接口的响应体。

    字段:
      matches —— 按 score 降序排列的结果列表，长度 ≤ top_k
    """
    matches: list[Match] = Field(description="检索结果，按融合分数降序排列")
