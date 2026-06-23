"""
LangGraph 节点函数。

每个节点接收当前 GraphState dict，返回增量更新 dict。
"""

from .route_node import route_node
from .retrieve_node import retrieve_node
from .grade_node import grade_node
from .web_search_node import web_search_node
from .analyze_node import analyze_node
from .code_write_node import code_write_node
from .execute_node import execute_node
from .repair_node import repair_node
from .report_node import report_node
from .validate_node import validate_node


MAX_WORKFLOW_STEPS = 20


def check_abort(state: dict) -> dict | None:
    """全局防死循环检查。返回 dict 时终止，None 时继续。"""
    step_count = state.get("_workflow_step_count", 0)
    if step_count >= MAX_WORKFLOW_STEPS:
        query = state.get("query", "")
        uploaded_files = state.get("uploaded_files", [])
        print(f"[LOG] [Abort] 工作流步数 {step_count} >= {MAX_WORKFLOW_STEPS}，强制终止")
        return {
            "completed": True,
            "current_step": "aborted",
            "errors": [f"工作流执行超过 {MAX_WORKFLOW_STEPS} 步，已自动终止，可能存在死循环"],
            "query": query,
            "uploaded_files": uploaded_files,
        }
    return None


__all__ = [
    "route_node",
    "retrieve_node",
    "grade_node",
    "web_search_node",
    "analyze_node",
    "code_write_node",
    "execute_node",
    "repair_node",
    "report_node",
    "validate_node",
    "check_abort",
    "MAX_WORKFLOW_STEPS",
]
