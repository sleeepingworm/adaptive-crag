"""
Grade 节点：调用 GraderAgent 评估证据是否足够。
"""

from datetime import datetime
from adaptive_crag.agents import GraderAgent
from adaptive_crag.config import load_llm_config


def grade_node(state: dict) -> dict:
    """评估证据是否足够"""
    _emit_event(state, "grade", "running", "正在评估证据充足性...")

    try:
        llm_config = load_llm_config()
        agent = GraderAgent(llm_config)
        result = agent.run(state)
        result["current_step"] = "grade"
        return result
    except Exception as e:
        return {
            "evidence_ready": False,
            "evidence_gap": f"评估失败: {str(e)}",
            "current_step": "grade",
            "errors": [f"GraderAgent 调用失败: {str(e)}"],
        }


def _emit_event(state: dict, step: str, status: str, message: str):
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
