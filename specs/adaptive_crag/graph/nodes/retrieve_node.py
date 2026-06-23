"""
Retrieve 节点：执行混合检索。
"""

from datetime import datetime


def retrieve_node(state: dict) -> dict:
    """执行混合检索"""
    _emit_event(state, "retrieve", "running", "正在检索文献...")

    try:
        from adaptive_crag.tools.hybrid_search import _hybrid_retriever

        if _hybrid_retriever is None:
            return {
                "retrieved_chunks": [],
                "current_step": "retrieve",
                "errors": ["检索器未初始化"],
            }

        query = state.get("query", "")
        results = _hybrid_retriever.search(query, top_k=10)

        return {
            "retrieved_chunks": results,
            "current_step": "retrieve",
        }
    except Exception as e:
        return {
            "retrieved_chunks": [],
            "current_step": "retrieve",
            "errors": [f"检索失败: {str(e)}"],
        }


def _emit_event(state: dict, step: str, status: str, message: str):
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
