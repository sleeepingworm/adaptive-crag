"""
Report 节点：调用 ReportAgent 生成最终报告。
"""

from datetime import datetime
from adaptive_crag.agents import ReportAgent
from adaptive_crag.config import load_llm_config


def report_node(state: dict) -> dict:
    """调用 ReportAgent 生成报告"""
    _emit_event(state, "report", "running", "正在生成研究报告...")

    try:
        llm_config = load_llm_config()
        agent = ReportAgent(llm_config)
        result = agent.run(state)
        result["current_step"] = "report"
        result["report_ready"] = bool(result.get("report"))
        return result
    except Exception as e:
        query = state.get("query", "")
        return {
            "report": f"# {query}\n\n## 摘要\n\n报告生成失败: {str(e)}\n",
            "report_ready": True,
            "current_step": "report",
            "errors": [f"ReportAgent 调用失败: {str(e)}"],
        }


def _emit_event(state: dict, step: str, status: str, message: str):
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
