"""
LangGraph 主工作流构建。

定义状态机图：节点注册、有向边连接、条件边逻辑。
"""

from adaptive_crag.graph.conditions import after_grade, after_analyze, after_execute
from adaptive_crag.graph.nodes import (
    route_node,
    retrieve_node,
    grade_node,
    web_search_node,
    analyze_node,
    code_write_node,
    execute_node,
    repair_node,
    report_node,
    validate_node,
)


def build_workflow() -> object:
    """
    构建 LangGraph 状态机。

    节点:
    - route -> retrieve -> grade -> (sufficient) analyze -> (need_code) code_write -> execute -> (success) report -> validate -> END
                                                                     |                    |-> (retry) repair -> execute
                                                                     |                    |-> (give_up) report
                                                                     |
                                                                  -> (no_code) report
                                                        -> (insufficient) web_search -> grade
    """
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(dict)  # 使用 dict 作为状态类型

    # 注册节点
    workflow.add_node("route", route_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade", grade_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("code_write", code_write_node)
    workflow.add_node("execute", execute_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("report", report_node)
    workflow.add_node("validate", validate_node)

    # 设置入口
    workflow.set_entry_point("route")

    # 有向边
    workflow.add_edge("route", "retrieve")
    workflow.add_edge("retrieve", "grade")
    workflow.add_conditional_edges("grade", after_grade, {
        "sufficient": "analyze",
        "insufficient": "web_search",
    })
    workflow.add_edge("web_search", "grade")
    workflow.add_conditional_edges("analyze", after_analyze, {
        "need_code": "code_write",
        "no_code": "report",
    })
    workflow.add_edge("code_write", "execute")
    workflow.add_conditional_edges("execute", after_execute, {
        "success": "report",
        "retry": "repair",
        "give_up": "report",
    })
    workflow.add_edge("repair", "execute")
    workflow.add_edge("report", "validate")
    workflow.add_edge("validate", END)

    return workflow


def run_workflow(initial_state: dict, callbacks: dict | None = None) -> dict:
    """
    执行工作流。

    Args:
        initial_state: 初始 GraphState dict
        callbacks: 可选回调 {"on_step_change": func, "on_tool_call": func}

    Returns:
        最终 GraphState dict
    """
    workflow = build_workflow()
    # 注入回调到 state
    if callbacks:
        initial_state["_callbacks"] = callbacks
    final_state = workflow.invoke(initial_state)
    return final_state
