"""Grade 节点：调用 GraderAgent 评估证据是否足够。"""

from .common import node_handler
from adaptive_crag.agents import GraderAgent
from adaptive_crag.config import load_llm_config


@node_handler("grade", "正在评估证据充足性...")
def grade_node(state: dict) -> dict:
    """评估证据是否足够"""
    loop_count = state.get("_grade_loop_count", 0)

    llm_config = load_llm_config()
    agent = GraderAgent(llm_config)
    result = agent.run(state)

    # 强制跳出：web_search 已执行过 2 次证据仍不足，强制推进
    if loop_count >= 2 and not result.get("evidence_ready", False):
        result["evidence_ready"] = True
        result["errors"] = result.get("errors", []) + ["证据不足但已超过最大重试次数，强制推进"]

    return result