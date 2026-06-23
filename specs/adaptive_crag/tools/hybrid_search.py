"""
混合检索工具。供 Retriever Agent 调用。
"""

from adaptive_crag.retrieval import HybridRetriever

# 全局检索器实例（由 application 层初始化）
_hybrid_retriever: HybridRetriever | None = None


def set_hybrid_retriever(retriever: HybridRetriever):
    """设置全局混合检索器实例"""
    global _hybrid_retriever
    _hybrid_retriever = retriever


def hybrid_search(params: dict) -> dict:
    """
    混合检索工具。

    params:
        query: str
        top_k: int = 10
        use_vector: bool = True
        use_bm25: bool = True
    """
    query = params.get("query", "")
    top_k = params.get("top_k", 10)
    use_vector = params.get("use_vector", True)
    use_bm25 = params.get("use_bm25", True)

    if not query:
        return {"success": False, "result": None, "error": "query 不能为空"}

    if _hybrid_retriever is None:
        return {"success": False, "result": None, "error": "检索器未初始化，请先上传文档"}

    try:
        results = _hybrid_retriever.search(query, top_k=top_k, use_vector=use_vector, use_bm25=use_bm25)
        return {
            "success": True,
            "result": {
                "query": query,
                "results": results,
                "total_found": len(results),
            },
        }
    except Exception as e:
        return {"success": False, "result": None, "error": f"检索失败: {str(e)}"}
