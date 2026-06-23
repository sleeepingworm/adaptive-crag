"""Repair 节点：调用 RepairAgent 修复失败的代码。"""

from .common import node_handler
from adaptive_crag.agents import RepairAgent
from adaptive_crag.config import load_llm_config


@node_handler("repair", "正在修复代码...")
def repair_node(state: dict) -> dict:
    """调用 RepairAgent 修复代码"""
    retry_count = state.get("retry_count", 0)

    llm_config = load_llm_config()
    agent = RepairAgent(llm_config)
    result = agent.run(state)
    result["current_step"] = f"repair_{retry_count + 1}"
    return result