"""
混合检索入口 — 同时执行向量检索和 BM25 检索，
合并去重后返回。
"""

from adaptive_crag.config.settings import RetrievalConfig
from .embedding_store import EmbeddingStore
from .bm25_store import BM25Store
from .rank_fusion import reciprocal_rank_fusion
from .reranker import Reranker
from .evidence_builder import build_evidence


class HybridRetriever:
    """
    混合检索入口。同时执行向量检索和 BM25 检索，
    合并去重、融合排序、Rerank、构建证据集合。
    """

    def __init__(self, embed_store: EmbeddingStore, bm25_store: BM25Store,
                 config: RetrievalConfig | None = None):
        self.embed_store = embed_store
        self.bm25_store = bm25_store
        self.config = config or RetrievalConfig()
        self._reranker = None

    def search(self, query: str, top_k: int | None = None,
               use_vector: bool = True, use_bm25: bool = True) -> list[dict]:
        """
        混合检索主入口。

        1. 向量检索 -> vec_results
        2. BM25 检索 -> bm25_results
        3. rank_fusion 融合排序
        4. reranker 重新排序（可选）
        5. evidence_builder 构建证据集合
        """
        if top_k is None:
            top_k = self.config.top_k

        vector_results = []
        bm25_results = []

        # 向量检索
        if use_vector:
            try:
                vector_results = self.embed_store.search(query, top_k=top_k * 2)
            except Exception:
                vector_results = []

        # BM25 检索
        if use_bm25:
            try:
                bm25_results = self.bm25_store.search(query, top_k=top_k * 2)
            except Exception:
                bm25_results = []

        # 混合融合
        if vector_results and bm25_results:
            fused = reciprocal_rank_fusion(
                vector_results, bm25_results,
                vector_weight=self.config.vector_weight,
                bm25_weight=self.config.bm25_weight,
            )
        elif vector_results:
            fused = vector_results
        else:
            fused = bm25_results

        # Rerank
        if fused and self.config.rerank_top_k > 0:
            try:
                reranked = self._get_reranker().rerank(query, fused, top_k=self.config.rerank_top_k)
                fused = reranked
            except Exception:
                pass  # rerank 失败降级

        # 截断
        fused = fused[:top_k]

        # 构建证据
        evidence = build_evidence(query, fused)

        return evidence["results"]

    def _get_reranker(self):
        """延迟加载 Reranker"""
        if self._reranker is None:
            self._reranker = Reranker()
        return self._reranker
