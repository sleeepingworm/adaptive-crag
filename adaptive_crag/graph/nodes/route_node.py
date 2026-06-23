"""Router 节点：调用 RouterAgent 进行任务规划。"""

from .common import node_handler
from adaptive_crag.agents import RouterAgent
from adaptive_crag.config import load_llm_config


@node_handler("route", "正在进行任务规划...")
def route_node(state: dict) -> dict:
    """调用 RouterAgent 进行任务规划"""
    llm_config = load_llm_config()
    agent = RouterAgent(llm_config)
    result = agent.run(state)
    return result