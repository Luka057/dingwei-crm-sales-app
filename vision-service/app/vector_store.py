"""
vector_store.py — 向量索引的抽象层与 FAISS 实现。

结构:
  VectorStore (ABC)  —— 抽象基类，定义统一接口
  FaissStore         —— 基于 faiss.IndexFlatIP 的余弦相似度索引（L2归一化向量 + 内积 = 余弦）
  QdrantStore        —— 占位桩（Phase-scale 选项，v1 未实现）

存储格式 (FaissStore.save):
  {path}/index.faiss    —— FAISS 二进制索引
  {path}/metadata.json  —— 与索引行一一对应的 payload 列表（JSON）
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod

import faiss
import numpy as np

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# 抽象基类
# ─────────────────────────────────────────────────────────────────

class VectorStore(ABC):
    """
    向量存储抽象接口。
    上层代码（search.py、index_samples.py）只依赖这个接口，
    可以安全地切换底层实现（FAISS → Qdrant 等）而无需修改业务逻辑。
    """

    @abstractmethod
    def add(self, vectors: np.ndarray, payloads: list[dict]) -> None:
        """
        批量添加向量及对应的 payload 元数据。
        vectors: float32 数组，形状 (N, embed_dim)，每行应已 L2 归一化
        payloads: 长度 N 的字典列表，与 vectors 行一一对应
        """
        ...

    @abstractmethod
    def search(self, vector: np.ndarray, k: int) -> list[tuple[float, dict]]:
        """
        近似最近邻检索。
        vector: float32 数组，形状 (embed_dim,)，已 L2 归一化
        k: 返回 top-k 结果
        返回: [(cosine_score, payload), ...] 按分数降序排列
        """
        ...

    @abstractmethod
    def save(self, path: str) -> None:
        """持久化索引到目录 path（目录不存在时自动创建）。"""
        ...

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> "VectorStore":
        """从目录 path 加载已保存的索引，返回实例。"""
        ...

    @property
    @abstractmethod
    def count(self) -> int:
        """当前索引中的向量数量。"""
        ...


# ─────────────────────────────────────────────────────────────────
# FAISS 实现
# ─────────────────────────────────────────────────────────────────

class FaissStore(VectorStore):
    """
    基于 faiss.IndexFlatIP（内积）的余弦相似度索引。

    原理:
      - 所有向量存入前都经过 L2 归一化（单位向量）
      - 单位向量的内积 = 余弦相似度（范围 -1..1，完全相同=1）
      - IndexFlatIP 是精确暴力搜索，小语料库（<10万）足够快
      - 大语料库可升级为 IndexIVFFlat 或 IndexHNSWFlat（仍用 IP metric）

    文件布局（save/load）:
      {path}/index.faiss    —— FAISS 序列化的索引
      {path}/metadata.json  —— payload 列表（与索引行对应）
    """

    _INDEX_FILE = "index.faiss"
    _META_FILE = "metadata.json"

    def __init__(self, embed_dim: int) -> None:
        self.embed_dim = embed_dim
        # IndexFlatIP: 精确内积检索，无需训练
        self._index: faiss.Index = faiss.IndexFlatIP(embed_dim)
        self._payloads: list[dict] = []   # 与 _index 行一一对应

    # ── 写 ──────────────────────────────────────────────────────

    def add(self, vectors: np.ndarray, payloads: list[dict]) -> None:
        """
        添加向量 + payload 到索引。
        vectors 应为 float32 且已 L2 归一化；
        如果未归一化，faiss 会按原始内积计算，结果不等于余弦相似度。
        """
        if len(vectors) != len(payloads):
            raise ValueError(
                f"vectors 行数 ({len(vectors)}) 与 payloads 长度 ({len(payloads)}) 不一致"
            )
        # FAISS 要求 C-contiguous float32 二维数组
        vecs = np.ascontiguousarray(vectors, dtype=np.float32)
        if vecs.ndim == 1:
            vecs = vecs.reshape(1, -1)
        self._index.add(vecs)              # 追加到内部存储
        self._payloads.extend(payloads)    # 保持行对齐

    # ── 读 ──────────────────────────────────────────────────────

    def search(self, vector: np.ndarray, k: int) -> list[tuple[float, dict]]:
        """
        用查询向量检索 top-k 最近邻。
        返回 [(cosine_score, payload), ...] 按分数降序。
        若索引为空，直接返回 []。
        """
        n = self._index.ntotal
        if n == 0:
            return []

        # 限制 k 不超过索引大小（否则 FAISS 会报错）
        actual_k = min(k, n)

        # FAISS 需要 (1, embed_dim) 的查询矩阵
        q = np.ascontiguousarray(vector, dtype=np.float32).reshape(1, -1)

        # 归一化查询向量（确保即使调用方忘记归一化也能正确计算余弦）
        norm = np.linalg.norm(q)
        if norm > 1e-10:
            q = q / norm

        scores, indices = self._index.search(q, actual_k)  # 返回 (1,k) 的数组

        results: list[tuple[float, dict]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                # FAISS 用 -1 表示"没有足够结果"，跳过
                continue
            results.append((float(score), self._payloads[int(idx)]))

        # 按分数降序排列（IndexFlatIP 通常已经是降序，但保险起见再排一次）
        results.sort(key=lambda x: x[0], reverse=True)
        return results

    # ── 持久化 ───────────────────────────────────────────────────

    def save(self, path: str) -> None:
        """序列化索引和 payload 到目录 path。"""
        os.makedirs(path, exist_ok=True)
        index_file = os.path.join(path, self._INDEX_FILE)
        meta_file = os.path.join(path, self._META_FILE)

        faiss.write_index(self._index, index_file)        # 写 FAISS 二进制
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self._payloads, f, ensure_ascii=False, indent=2)

        logger.info("[FaissStore] 已保存 %d 条向量 → %s", self._index.ntotal, path)

    @classmethod
    def load(cls, path: str) -> "FaissStore":
        """从目录 path 加载索引和 payload，返回 FaissStore 实例。"""
        index_file = os.path.join(path, cls._INDEX_FILE)
        meta_file = os.path.join(path, cls._META_FILE)

        index = faiss.read_index(index_file)              # 读 FAISS 二进制
        with open(meta_file, encoding="utf-8") as f:
            payloads = json.load(f)

        store = cls.__new__(cls)
        store.embed_dim = index.d                          # 从索引读取维度
        store._index = index
        store._payloads = payloads

        logger.info("[FaissStore] 已加载 %d 条向量 ← %s", index.ntotal, path)
        return store

    @property
    def count(self) -> int:
        """当前索引中的向量数量。"""
        return int(self._index.ntotal)


# ─────────────────────────────────────────────────────────────────
# Qdrant 占位桩（Phase-scale 选项）
# ─────────────────────────────────────────────────────────────────

class QdrantStore(VectorStore):
    """
    Qdrant 向量数据库接口（占位实现）。

    为什么存在:
      Qdrant 支持持久化、过滤、分布式部署，适合百万级语料库。
      当样本量超过 FaissStore 的内存上限时，可切换到 Qdrant。

    当前状态: v1 未实现。实现时需要:
      pip install qdrant-client
      docker run -p 6333:6333 qdrant/qdrant
    """

    def add(self, vectors: np.ndarray, payloads: list[dict]) -> None:
        raise NotImplementedError("Qdrant backend: Phase-scale option, not implemented in v1")

    def search(self, vector: np.ndarray, k: int) -> list[tuple[float, dict]]:
        raise NotImplementedError("Qdrant backend: Phase-scale option, not implemented in v1")

    def save(self, path: str) -> None:
        raise NotImplementedError("Qdrant backend: Phase-scale option, not implemented in v1")

    @classmethod
    def load(cls, path: str) -> "QdrantStore":
        raise NotImplementedError("Qdrant backend: Phase-scale option, not implemented in v1")

    @property
    def count(self) -> int:
        raise NotImplementedError("Qdrant backend: Phase-scale option, not implemented in v1")


# ─────────────────────────────────────────────────────────────────
# 工厂函数
# ─────────────────────────────────────────────────────────────────

def build_store(backend: str, embed_dim: int) -> VectorStore:
    """根据 settings.vector_store 创建空的向量存储实例。"""
    if backend == "faiss":
        return FaissStore(embed_dim=embed_dim)
    elif backend == "qdrant":
        return QdrantStore()
    else:
        raise ValueError(f"未知的 vector_store 后端: {backend!r}（支持: faiss, qdrant）")
