"""
Web Search 节点：执行联网搜索补偿。
"""

from datetime import datetime
from adaptive_crag.tools.web_search import web_search


def web_search_node(state: dict) -> dict:
    """执行联网搜索"""
    _emit_event(state, "web_search", "running", "正在联网搜索补充信息...")

    query = state.get("query", "")
    gap = state.get("evidence_gap", "")

    # 如果有证据缺口，用缺口描述作为搜索查询
    search_query = f"{query} {gap}" if gap else query

    try:
        result = web_search({"query": search_query, "max_results": 5})
        if result.get("success"):
            web_results = result["result"].get("results", [])
        else:
            web_results = []

        return {
            "web_search_results": web_results,
            "current_step": "web_search",
        }
    except Exception as e:
        return {
            "web_search_results": [],
            "current_step": "web_search",
            "errors": [f"联网搜索失败: {str(e)}"],
        }


def _emit_event(state: dict, step: str, status: str, message: str):
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
