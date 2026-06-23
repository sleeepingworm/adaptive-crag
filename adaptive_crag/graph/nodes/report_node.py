"""Report 节点：调用 ReportAgent 生成最终报告。"""

from .common import node_handler
from adaptive_crag.agents import ReportAgent
from adaptive_crag.config import load_llm_config


@node_handler("report", "正在生成研究报告...")
def report_node(state: dict) -> dict:
    """调用 ReportAgent 生成报告"""
    llm_config = load_llm_config()
    agent = ReportAgent(llm_config)
    result = agent.run(state)
    result["report_ready"] = bool(result.get("report"))
    return result