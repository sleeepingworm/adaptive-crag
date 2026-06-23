"""
Router 节点：调用 RouterAgent 进行任务规划。
"""

from datetime import datetime
from adaptive_crag.agents import RouterAgent
from adaptive_crag.config import load_llm_config


def route_node(state: dict) -> dict:
    """调用 RouterAgent 进行任务规划"""
    _emit_event(state, "route", "running", "正在进行任务规划...")

    try:
        llm_config = load_llm_config()
        agent = RouterAgent(llm_config)
        result = agent.run(state)
        result["current_step"] = "route"
        return result
    except Exception as e:
        return {
            "plan": {
                "original_query": state.get("query", ""),
                "sub_tasks": [{"type": "literature_search", "description": state.get("query", ""), "files": state.get("uploaded_files", [])}],
                "requires_code": False,
                "requires_web_search": False,
                "output_format": "markdown",
            },
            "current_step": "route",
            "errors": [f"RouterAgent 调用失败: {str(e)}"],
        }


def _emit_event(state: dict, step: str, status: str, message: str):
    """触发事件回调"""
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
