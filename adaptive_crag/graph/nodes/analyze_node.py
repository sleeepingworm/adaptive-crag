"""Analyze 节点：调用 AnalyzerAgent 制定分析方案。"""

from .common import node_handler
from adaptive_crag.agents import AnalyzerAgent
from adaptive_crag.config import load_llm_config


@node_handler("analyze", "正在制定分析方案...")
def analyze_node(state: dict) -> dict:
    """调用 AnalyzerAgent 制定分析方案"""
    llm_config = load_llm_config()
    agent = AnalyzerAgent(llm_config)
    result = agent.run(state)
    return result