"""Validate 节点：调用 ValidatorAgent 校验引用。"""

from .common import node_handler
from adaptive_crag.agents import ValidatorAgent
from adaptive_crag.config import load_llm_config


@node_handler("validate", "正在校验引用来源...")
def validate_node(state: dict) -> dict:
    """调用 ValidatorAgent 校验引用"""
    llm_config = load_llm_config()
    agent = ValidatorAgent(llm_config)
    result = agent.run(state)
    result["completed"] = True
    return result