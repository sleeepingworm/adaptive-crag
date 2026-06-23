"""
adaptive_crag.retrieval - 检索层
===============================
向量检索 + BM25 关键词检索 + 混合融合 + Rerank + 证据构建。
"""

from .embedding_store import EmbeddingStore
from .bm25_store import BM25Store
from .hybrid_retriever import HybridRetriever
from .rank_fusion import reciprocal_rank_fusion
from .reranker import Reranker
from .evidence_builder import build_evidence

__all__ = [
    "EmbeddingStore",
    "BM25Store",
    "HybridRetriever",
    "reciprocal_rank_fusion",
    "Reranker",
    "build_evidence",
]
