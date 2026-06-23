"""
混合检索工具。供 Retriever Agent 调用。
不再依赖模块级全局变量 —— retriever 通过 params 传入。
"""

from adaptive_crag.retrieval import HybridRetriever


def hybrid_search(params: dict) -> dict:
    """
    混合检索工具。

    params:
        query: str
        top_k: int = 10
        use_vector: bool = True
        use_bm25: bool = True
        _retriever: HybridRetriever | None = None  (由调用方传入，不再依赖全局)
    """
    query = params.get("query", "")
    top_k = params.get("top_k", 10)
    use_vector = params.get("use_vector", True)
    use_bm25 = params.get("use_bm25", True)
    retriever = params.get("retriever")

    if not query:
        return {"success": False, "result": None, "error": "query 不能为空"}

    if retriever is None:
        return {"success": False, "result": None, "error": "检索器未初始化，请先上传文档"}

    try:
        results = retriever.search(query, top_k=top_k, use_vector=use_vector, use_bm25=use_bm25)
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