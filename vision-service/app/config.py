"""
config.py — 环境驱动的服务配置。
所有字段均可通过环境变量覆盖（大写字段名，pydantic-settings 自动解析）。

快速启动 (mock 模式，无需 torch/transformers):
  VISION_USE_MOCK=true uvicorn app.main:app ...

真实模型模式 (DINOv3，默认):
  pip install -r requirements.txt
  huggingface-cli login   # 粘贴 HF token（需先在网页点 Agree）
  VISION_USE_MOCK=false uvicorn app.main:app ...
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    服务全局配置。
    所有字段都可以通过同名环境变量覆盖，前缀为 VISION_。
    例如: VISION_USE_MOCK=false
    """

    # --- 运行模式 ---
    # True  → 使用 MockEmbedder（确定性伪向量，无需 torch/transformers）
    # False → 尝试加载 SiglipEmbedder，失败则回退 MockEmbedder 并打印警告
    use_mock: bool = True

    # --- 模型配置 (仅 use_mock=False 时生效) ---
    # HuggingFace 模型 ID 或本地目录路径
    # 默认 DINOv3 ViT-B/16 (86M 参数, 768 维, ~350MB)
    # 路径包含 "siglip" 时自动切回 SiglipEmbedder（向后兼容）
    model_path: str = "facebook/dinov3-vitb16-pretrain-lvd1689m"
    # "auto" → 自动选择 cuda/mps/cpu；也可显式指定 "cpu"/"cuda"/"mps"
    device: str = "auto"
    # 嵌入向量维度（DINOv3 ViT-B/16: 768；ViT-L: 1024；ViT-S: 384）
    embed_dim: int = 768

    # --- 向量数据库 ---
    # 目前支持 "faiss"；"qdrant" 为占位桩
    vector_store: str = "faiss"
    # 存放 index.faiss + metadata.json 的目录
    index_path: str = "./index"

    # --- 语料库 ---
    # 图片文件所在目录（同时挂载为 /images 静态路由）
    images_dir: str = "./corpus"

    # --- 检索参数 ---
    # ANN 阶段召回的候选数量（之后用融合分数重排，再取 top_k）
    top_k_ann: int = 50

    # --- 融合权重 ---
    # 三路相似度的加权比例，总和不要求 =1（fuse() 内部直接加权求和后 clamp）
    # 可通过环境变量传入 JSON 字符串，例如:
    #   VISION_FUSION_WEIGHTS='{"image":0.6,"text":0.2,"process":0.2}'
    # DINOv3 模式默认: 纯图像（DINOv3 无文字侧；工艺改硬过滤，详见 spec 2026-05-29）
    fusion_weights: dict = {"image": 1.0, "text": 0.0, "process": 0.0}

    # --- 安全 ---
    # 若设置，则 POST /sample-search 需要 Authorization: Bearer <token>
    # None 表示不鉴权（开发/内网环境默认关闭）
    service_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="VISION_",          # 所有环境变量以 VISION_ 开头
        env_file=".env",               # 也可在 vision-service/.env 中写配置
        env_file_encoding="utf-8",
        extra="ignore",                # 忽略未知环境变量
    )

    @field_validator("fusion_weights", mode="before")
    @classmethod
    def parse_fusion_weights(cls, v: Any) -> Any:
        """允许从环境变量传入 JSON 字符串，例如 '{"image":0.5,"text":0.3,"process":0.2}'"""
        if isinstance(v, str):
            return json.loads(v)
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    单例工厂：整个进程只实例化一次 Settings，之后直接命中缓存。
    FastAPI 的 Depends(get_settings) 会调用此函数。
    """
    return Settings()
