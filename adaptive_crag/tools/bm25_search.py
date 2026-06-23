"""
纯 BM25 关键字检索工具。
不再依赖 hybrid_search 模块的全局变量 —— retriever 通过 params 传入。
"""


def bm25_search(params: dict) -> dict:
    """
    纯 BM25 关键字检索工具。

    params:
        query: str
        top_k: int = 10
        _retriever: HybridRetriever | None = None  (由调用方传入)
    """
    query = params.get("query", "")
    top_k = params.get("top_k", 10)
    retriever = params.get("retriever")

    if not query:
        return {"success": False, "result": None, "error": "query 不能为空"}

    if retriever is None:
        return {"success": False, "result": None, "error": "检索器未初始化，请先上传文档"}

    try:
        results = retriever.search(query, top_k=top_k, use_vector=False, use_bm25=True)
        return {
            "success": True,
            "result": {
                "query": query,
                "results": results,
                "total_found": len(results),
            },
        }
    except Exception as e:
        return {"success": False, "result": None, "error": f"关键词检索失败: {str(e)}"}