"""Web Search 节点：执行联网搜索补偿。"""

from .common import node_handler
from adaptive_crag.tools.web_search import web_search as _web_search_fn


@node_handler("web_search", "正在联网搜索补充信息...")
def web_search_node(state: dict) -> dict:
    """执行联网搜索"""
    query = state.get("query", "")
    gap = state.get("evidence_gap", "")

    search_query = f"{query} {gap}" if gap else query

    result = _web_search_fn({"query": search_query, "max_results": 5})
    if result.get("success"):
        web_results = result["result"].get("results", [])
    else:
        web_results = []

    return {
        "web_search_results": web_results,
        "_grade_loop_count": state.get("_grade_loop_count", 0) + 1,
    }