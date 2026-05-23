"""
fusion.py — 多路相似度融合层。

═══════════════════════════════════════════════════════════════════
  算法工程师交接线 (ENGINEER SEAM)
═══════════════════════════════════════════════════════════════════
本文件负责将三路相似度信号合并为最终排序分数:
  image_sim   —— 图片视觉相似度（来自 FAISS 余弦检索）
  text_sim    —— 文字描述相似度（查询向量 vs 样本文本嵌入的余弦）
  process_sim —— 工艺参数匹配度（精确字段对比）

替换说明:
  - fuse() 是融合算法的主入口，可以替换为 MLP re-ranker、学习排序模型等
  - process_similarity() 可以扩展支持数值范围比较（宽度容差 ±2mm 等）
  - 权重 fusion_weights 通过环境变量 VISION_FUSION_WEIGHTS 动态配置
═══════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# 工艺参数匹配度
# ─────────────────────────────────────────────────────────────────

_FILTER_FIELDS = ("width", "tension", "ribbon_type")

def process_similarity(filters: dict, metadata: dict) -> float:
    """
    计算查询过滤条件与样本元数据的工艺匹配度。

    算法:
      1. 从 filters 中取出非空字段（width / tension / ribbon_type）
      2. 对每个非空字段，检查是否与 metadata 中同名字段"宽松匹配"
         宽松匹配规则: 双方均转小写去首尾空格后，
                       A 包含 B 或 B 包含 A（允许 "黑色" 匹配 "黑色提花"）
      3. 匹配数 / 总过滤字段数 → 匹配率 [0.0, 1.0]

    边界情况:
      - 无任何过滤字段 → 返回 0.0
        （不代表"完全不匹配"，而是"无工艺约束"；
         fuse() 中 process 权重可以调为 0 来忽略此路信号）
      - 字段在 metadata 中不存在或为空 → 视为不匹配

    >>> ENGINEER SEAM: 可在此处添加数值范围容差，例如宽度 ±2mm <<<
    """
    active_filters: list[tuple[str, str]] = []

    for field in _FILTER_FIELDS:
        val = filters.get(field)
        if val is not None and str(val).strip():
            active_filters.append((field, str(val).strip().lower()))

    if not active_filters:
        # 没有过滤条件 → 工艺匹配度无意义，返回 0.0
        # 注意: 这不会惩罚样本，因为 fuse() 的加权求和中 process_sim * weight 也为 0
        return 0.0

    matched = 0
    for field, query_val in active_filters:
        sample_val = metadata.get(field)
        if sample_val is None:
            continue
        sample_val = str(sample_val).strip().lower()
        # 宽松匹配：包含关系（双向）
        if query_val in sample_val or sample_val in query_val:
            matched += 1

    return matched / len(active_filters)


# ─────────────────────────────────────────────────────────────────
# 融合函数
# ─────────────────────────────────────────────────────────────────

def fuse(
    image_sim: float,
    text_sim: float,
    process_sim: float,
    weights: dict,
) -> float:
    """
    将三路相似度线性加权融合为最终分数。

    参数:
      image_sim   —— 图片余弦相似度，范围 [-1, 1]（通常 >0）
      text_sim    —— 文本余弦相似度，范围 [-1, 1]
      process_sim —— 工艺匹配率，范围 [0, 1]
      weights     —— {"image": w1, "text": w2, "process": w3}
                     各权重不要求归一化，可以不为 1

    返回:
      融合分数，clamp 到 [0.0, 1.0]

    默认权重含义（可通过 VISION_FUSION_WEIGHTS 调整）:
      image:0.5   视觉外观最重要
      text:0.3    文字描述次之
      process:0.2 工艺参数作为辅助信号（无过滤时此项为 0）

    >>> ENGINEER SEAM: 可将此函数替换为学习排序模型（LambdaMART / MLP re-ranker）<<<
    只需保持函数签名不变，输出范围 [0,1] 即可。
    """
    w_img = weights.get("image", 0.5)
    w_txt = weights.get("text", 0.3)
    w_proc = weights.get("process", 0.2)

    # 加权求和
    score = w_img * image_sim + w_txt * text_sim + w_proc * process_sim

    # clamp 到 [0, 1]（余弦值可能为负，加权后也可能溢出）
    return float(max(0.0, min(1.0, score)))
