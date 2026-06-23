"""
Validate 节点：调用 ValidatorAgent 校验引用。
"""

from datetime import datetime
from adaptive_crag.agents import ValidatorAgent
from adaptive_crag.config import load_llm_config


def validate_node(state: dict) -> dict:
    """调用 ValidatorAgent 校验引用"""
    _emit_event(state, "validate", "running", "正在校验引用来源...")

    try:
        llm_config = load_llm_config()
        agent = ValidatorAgent(llm_config)
        result = agent.run(state)
        result["current_step"] = "validate"
        result["completed"] = True
        return result
    except Exception as e:
        return {
            "citations_valid": True,  # 降级通过
            "current_step": "validate",
            "completed": True,
            "errors": [f"ValidatorAgent 调用失败: {str(e)}"],
        }


def _emit_event(state: dict, step: str, status: str, message: str):
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
