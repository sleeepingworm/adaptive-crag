"""
Repair 节点：调用 RepairAgent 修复失败的代码。
"""

from datetime import datetime
from adaptive_crag.agents import RepairAgent
from adaptive_crag.config import load_llm_config


def repair_node(state: dict) -> dict:
    """调用 RepairAgent 修复代码"""
    retry_count = state.get("retry_count", 0)
    _emit_event(state, "repair", "running", f"正在修复代码（第 {retry_count + 1} 次重试）...")

    try:
        llm_config = load_llm_config()
        agent = RepairAgent(llm_config)
        result = agent.run(state)
        result["current_step"] = f"repair_{retry_count + 1}"
        return result
    except Exception as e:
        retry_count = state.get("retry_count", 0) + 1
        return {
            "code": state.get("code", ""),  # 保留原代码
            "retry_count": retry_count,
            "current_step": f"repair_failed_{retry_count}",
            "errors": [f"RepairAgent 调用失败: {str(e)}"],
        }


def _emit_event(state: dict, step: str, status: str, message: str):
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
