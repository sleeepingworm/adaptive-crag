"""
Analyze 节点：调用 AnalyzerAgent 制定分析方案。
"""

from datetime import datetime
from adaptive_crag.agents import AnalyzerAgent
from adaptive_crag.config import load_llm_config


def analyze_node(state: dict) -> dict:
    """调用 AnalyzerAgent 制定分析方案"""
    _emit_event(state, "analyze", "running", "正在制定分析方案...")

    try:
        llm_config = load_llm_config()
        agent = AnalyzerAgent(llm_config)
        result = agent.run(state)
        result["current_step"] = "analyze"
        return result
    except Exception as e:
        return {
            "code_plan": "",
            "current_step": "analyze",
            "errors": [f"AnalyzerAgent 调用失败: {str(e)}"],
        }


def _emit_event(state: dict, step: str, status: str, message: str):
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
