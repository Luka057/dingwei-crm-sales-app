"""
model.py — 嵌入模型层。

═══════════════════════════════════════════════════════════════════
  算法工程师交接线 (ENGINEER SEAM)
═══════════════════════════════════════════════════════════════════
本文件定义四个对象:
  1. Embedder       —— Protocol（接口规范），其余代码只依赖这个接口
  2. MockEmbedder   —— 本地可立即运行的确定性占位实现（无 torch）
  3. DinoV3Embedder —— [默认真实模型] DINOv3 ViT-B/16 (Meta 2025)
                        86M 参数 / 768 维 / 颜色无关 / 纹理优先 / 商用 license
                        见 docs/superpowers/specs/2026-05-29-ai-zhaoban-algorithm-design.md
  4. SiglipEmbedder —— [对比参考] 原 SigLIP2 实现（保留供未来对照）

要启用 DINOv3 真实模型:
  1. pip install -r requirements.txt   (会装 torch + transformers)
  2. 去 https://huggingface.co/facebook/dinov3-vitb16-pretrain-lvd1689m 点 "Agree and access"
  3. huggingface-cli login  (粘贴 HF token)
  4. VISION_USE_MOCK=false uvicorn app.main:app --port 8077
═══════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import hashlib
import logging
from typing import Protocol, runtime_checkable

import numpy as np
from PIL import Image

from app.config import Settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# 接口定义
# ─────────────────────────────────────────────────────────────────

@runtime_checkable
class Embedder(Protocol):
    """
    嵌入器接口规范。
    所有实现都必须满足:
      - 返回 float32 numpy 数组，形状 (embed_dim,)
      - 向量已 L2 归一化（单位向量），可直接用内积计算余弦相似度
    """

    def embed_image(self, img: Image.Image) -> np.ndarray:
        """将 PIL 图片编码为 L2 归一化的浮点向量。"""
        ...

    def embed_text(self, text: str) -> np.ndarray:
        """将文本字符串编码为 L2 归一化的浮点向量（与图片向量同维度）。"""
        ...


# ─────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────

def _l2_normalize(v: np.ndarray) -> np.ndarray:
    """L2 归一化：v / ||v||。若向量为零则返回全零向量（避免除零）。"""
    norm = np.linalg.norm(v)
    if norm < 1e-10:
        return v
    return v / norm


def _bytes_to_unit_vector(data: bytes, dim: int) -> np.ndarray:
    """
    确定性地将任意字节序列映射到 dim 维单位向量。
    步骤:
      1. SHA-256 hash → 32 字节 → 取前 4 字节转换为 uint32 作为随机种子
      2. 用种子初始化 numpy 随机生成器 → 生成标准正态向量
      3. L2 归一化

    【重要】相同输入 → 相同输出（确定性），不同输入 → 几乎不同向量（但无语义）。
    MockEmbedder 的向量没有真实的视觉/语义相似性，仅用于验证系统管道是否通畅。
    """
    digest = hashlib.sha256(data).digest()          # 32 字节
    seed = int.from_bytes(digest[:4], "big")         # 取 4 字节 → uint32 种子
    rng = np.random.default_rng(seed)                # 确定性随机生成器
    vec = rng.standard_normal(dim).astype(np.float32)
    return _l2_normalize(vec)


# ─────────────────────────────────────────────────────────────────
# 占位实现（Mock）
# ─────────────────────────────────────────────────────────────────

class MockEmbedder:
    """
    确定性占位嵌入器。
    【用途】在没有 torch/transformers 的环境下立即运行，验证向量检索管道。
    【局限】图片之间没有真实的视觉相似性——视觉上相似的图片不会在向量空间中聚类。
            这是 placeholder，不要用于生产推荐。
    【替换方式】设置 VISION_USE_MOCK=false，安装 torch+transformers，
               SiglipEmbedder 会自动接管。
    """

    def __init__(self, embed_dim: int = 768) -> None:
        self.embed_dim = embed_dim
        logger.info("[MockEmbedder] 启动 — embed_dim=%d（确定性哈希向量，无真实语义）", embed_dim)

    def embed_image(self, img: Image.Image) -> np.ndarray:
        """
        图片 → 向量:
          1. 缩放至 32×32（减小字节量，保留大致色调信息作为哈希输入）
          2. tobytes() → 哈希 → 种子 → 随机单位向量
        """
        small = img.resize((32, 32), Image.BILINEAR).convert("RGB")  # 统一为 RGB
        return _bytes_to_unit_vector(small.tobytes(), self.embed_dim)

    def embed_text(self, text: str) -> np.ndarray:
        """文本 → 向量：UTF-8 字节 → 哈希 → 种子 → 随机单位向量。"""
        return _bytes_to_unit_vector(text.encode("utf-8"), self.embed_dim)


# ─────────────────────────────────────────────────────────────────
# 真实 DINOv3 实现（当前默认 — 详见 spec 2026-05-29）
# ─────────────────────────────────────────────────────────────────

class DinoV3Embedder:
    """
    基于 HuggingFace transformers 的 DINOv3 嵌入器。
    需要: pip install torch transformers>=4.45 accelerate

    特点（对比 SigLIP2）:
      - 纯视觉自监督，无文字侧 → embed_text 返回零向量（fusion 中 text 权重应为 0）
      - 颜色无关 + 纹理优先 → 适合织带这种细粒度工业纹理产品
      - 内置 register tokens → 对脏背景/手机现场拍鲁棒

    >>> ENGINEER SEAM: 升级 DINOv3 微调权重 / 更换 ViT-L 时只改 __init__ 与 embed_image <<<
    """

    def __init__(self, model_path: str, device: str, embed_dim: int) -> None:
        # 延迟导入：使本文件在无 torch 环境下仍可被解析（MockEmbedder 路径）
        import torch
        from transformers import AutoImageProcessor, AutoModel

        # 自动设备选型：CUDA > MPS > CPU
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.device = torch.device(device)
        self.embed_dim = embed_dim

        logger.info("[DinoV3Embedder] 加载模型 %s → device=%s", model_path, device)

        # >>> ENGINEER SEAM: 替换为你的 DINOv3 微调 checkpoint 时改这里 <<<
        # AutoImageProcessor 负责输入预处理（resize / 归一化）
        # AutoModel 加载 DINOv3 backbone，输出 pooler_output (CLS token, shape [1, 768])
        self.processor = AutoImageProcessor.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path).to(self.device).eval()
        # >>> END ENGINEER SEAM <<<

        logger.info("[DinoV3Embedder] 模型加载完成 — 参数量约 86M, 嵌入维度 %d", embed_dim)

    def embed_image(self, img: Image.Image) -> np.ndarray:
        """
        图片 → L2 归一化的 768 维向量。

        DINOv3 输出 outputs.pooler_output 即为 CLS token（整张图的全局表征），
        直接拿来 L2 归一化就是可用的相似度嵌入。
        """
        import torch

        # 预处理：DINOv3 自带的 processor 会把图片缩放到 224×224 + 归一化
        inputs = self.processor(images=img, return_tensors="pt").to(self.device)
        # inference_mode 比 no_grad 更省内存（PyTorch 1.9+）
        with torch.inference_mode():
            outputs = self.model(**inputs)
        # pooler_output: shape (1, 768) — CLS token 经过 layer norm 后的输出
        vec = outputs.pooler_output[0].cpu().float().numpy()

        return _l2_normalize(vec)

    def embed_text(self, text: str) -> np.ndarray:
        """
        DINOv3 没有文本编码器 → 返回零向量。

        【设计意图】保持 Embedder Protocol 兼容（search.py 仍会调 embed_text），
        但由于 fusion.py 中 text 权重应配为 0（见 spec 2026-05-29），
        零向量在加权求和里自然贡献 0，不污染最终分数。

        如果未来想要文字检索：可换成独立的 sentence-transformers 模型。
        """
        return np.zeros(self.embed_dim, dtype=np.float32)


# ─────────────────────────────────────────────────────────────────
# 原 SigLIP 实现（保留对照 — 当前不启用）
# ─────────────────────────────────────────────────────────────────

class SiglipEmbedder:
    """
    基于 HuggingFace transformers 的 SigLIP/SigLIP2 嵌入器。
    需要: pip install torch transformers

    ┌──────────────────────────────────────────────────────────────┐
    │  >>> ENGINEER SEAM: replace with your SigLIP2 weights <<<   │
    │  修改 _encode_image / _encode_text 中的推理逻辑即可接入     │
    │  自定义权重或更新到 SigLIP2。                               │
    └──────────────────────────────────────────────────────────────┘
    """

    def __init__(self, model_path: str, device: str, embed_dim: int) -> None:
        # >>> ENGINEER SEAM: replace with your SigLIP2 weights/inference <<<
        # 以下为标准 HuggingFace SigLIP 加载流程，可替换为自定义加载逻辑
        import torch
        from transformers import AutoProcessor, AutoModel

        # 自动选择设备
        if device == "auto":
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

        self.device = torch.device(device)
        self.embed_dim = embed_dim

        logger.info("[SiglipEmbedder] 加载模型 %s → device=%s", model_path, device)

        # >>> ENGINEER SEAM: 替换为你的 SigLIP2 processor/model 加载 <<<
        self.processor = AutoProcessor.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path).to(self.device).eval()

        logger.info("[SiglipEmbedder] 模型加载完成")
        # >>> END ENGINEER SEAM <<<

    def embed_image(self, img: Image.Image) -> np.ndarray:
        """
        图片 → L2 归一化向量。

        >>> ENGINEER SEAM: 如果你的 SigLIP2 用不同的 API 出图像特征，在这里修改 <<<
        """
        import torch

        # >>> ENGINEER SEAM: 替换为你的图像推理逻辑 <<<
        inputs = self.processor(images=img, return_tensors="pt").to(self.device)
        with torch.no_grad():
            # get_image_features 返回 (1, embed_dim) 的特征向量
            feats = self.model.get_image_features(**inputs)
        vec = feats[0].cpu().float().numpy()
        # >>> END ENGINEER SEAM <<<

        return _l2_normalize(vec)

    def embed_text(self, text: str) -> np.ndarray:
        """
        文本 → L2 归一化向量（与图片向量同一空间，可直接比较）。

        >>> ENGINEER SEAM: 如果你的 SigLIP2 用不同的 API 出文本特征，在这里修改 <<<
        """
        import torch

        # >>> ENGINEER SEAM: 替换为你的文本推理逻辑 <<<
        inputs = self.processor(text=[text], return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            feats = self.model.get_text_features(**inputs)
        vec = feats[0].cpu().float().numpy()
        # >>> END ENGINEER SEAM <<<

        return _l2_normalize(vec)


# ─────────────────────────────────────────────────────────────────
# 工厂函数
# ─────────────────────────────────────────────────────────────────

def build_embedder(settings: Settings) -> Embedder:
    """
    根据配置选择并构建嵌入器。

    决策逻辑:
      use_mock=True   → MockEmbedder（默认，无任何重型依赖）
      use_mock=False  → 尝试 SiglipEmbedder
                          成功 → 返回 SiglipEmbedder
                          失败（ImportError / 模型加载错误）
                              → 打印醒目警告，回退 MockEmbedder
    """
    if settings.use_mock:
        logger.info("═" * 60)
        logger.info("  [VISION MODE] MOCK（VISION_USE_MOCK=true）")
        logger.info("  向量为确定性哈希占位，无真实语义相似性")
        logger.info("  生产环境请设置 VISION_USE_MOCK=false 并安装 torch+transformers")
        logger.info("═" * 60)
        return MockEmbedder(embed_dim=settings.embed_dim)

    # 尝试加载真实模型（默认 DINOv3；如果 model_path 含 "siglip" 字样则走 SiglipEmbedder）
    try:
        if "siglip" in settings.model_path.lower():
            embedder = SiglipEmbedder(
                model_path=settings.model_path,
                device=settings.device,
                embed_dim=settings.embed_dim,
            )
            mode_name = "SIGLIP"
        else:
            embedder = DinoV3Embedder(
                model_path=settings.model_path,
                device=settings.device,
                embed_dim=settings.embed_dim,
            )
            mode_name = "DINOv3"

        logger.info("═" * 60)
        logger.info("  [VISION MODE] %s（真实模型）", mode_name)
        logger.info("  model_path=%s  device=%s", settings.model_path, settings.device)
        logger.info("═" * 60)
        return embedder

    except ImportError as exc:
        logger.warning("═" * 60)
        logger.warning("  [VISION MODE] 警告：torch/transformers 未安装，回退 MOCK")
        logger.warning("  ImportError: %s", exc)
        logger.warning("  如需真实模型: pip install torch transformers")
        logger.warning("═" * 60)
        return MockEmbedder(embed_dim=settings.embed_dim)

    except Exception as exc:  # noqa: BLE001
        logger.warning("═" * 60)
        logger.warning("  [VISION MODE] 警告：模型加载失败，回退 MOCK")
        logger.warning("  Error: %s", exc)
        logger.warning("═" * 60)
        return MockEmbedder(embed_dim=settings.embed_dim)
