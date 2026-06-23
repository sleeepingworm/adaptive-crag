"""
纯 BM25 关键字检索工具。
"""

from .hybrid_search import _hybrid_retriever


def bm25_search(params: dict) -> dict:
    """
    纯 BM25 关键字检索工具。

    params:
        query: str
        top_k: int = 10
    """
    query = params.get("query", "")
    top_k = params.get("top_k", 10)

    if not query:
        return {"success": False, "result": None, "error": "query 不能为空"}

    if _hybrid_retriever is None:
        return {"success": False, "result": None, "error": "检索器未初始化，请先上传文档"}

    try:
        results = _hybrid_retriever.search(query, top_k=top_k, use_vector=False, use_bm25=True)
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
