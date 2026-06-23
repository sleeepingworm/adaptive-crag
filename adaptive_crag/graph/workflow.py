"""
LangGraph 主工作流构建。

步骤由 PIPELINE_STEPS 配置列表驱动，build_workflow() 不再硬编码顺序。
"""

from dataclasses import dataclass, field
from typing import Callable

from langgraph.graph import StateGraph, END

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


@dataclass
class PipelineStep:
    """工作流中的一个步骤"""
    name: str                      # 步骤标识，如 "route"
    node_func: Callable            # 节点函数
    next_step: str | None = None   # 无条件跳转目标，None 表示 END
    conditional: tuple | None = None  # (条件函数, 分支映射) 或 None
    is_entry: bool = False         # 是否为入口步骤


# ============================================================
# 流水线配置 —— 增减步骤只需改这个列表，build_workflow() 不用动
# ============================================================
PIPELINE_STEPS: list[PipelineStep] = [
    PipelineStep("route",       route_node,       next_step="retrieve",   is_entry=True),
    PipelineStep("retrieve",    retrieve_node,    next_step="grade"),
    PipelineStep("grade",       grade_node,       conditional=(after_grade, {
        "sufficient": "analyze",
        "insufficient": "web_search",
        END: END,
    })),
    PipelineStep("web_search",  web_search_node,  next_step="grade"),
    PipelineStep("analyze",     analyze_node,     conditional=(after_analyze, {
        "need_code": "code_write",
        "no_code": "report",
        END: END,
    })),
    PipelineStep("code_write",  code_write_node,  next_step="execute"),
    PipelineStep("execute",     execute_node,     conditional=(after_execute, {
        "success": "report",
        "retry": "repair",
        "give_up": "report",
        END: END,
    })),
    PipelineStep("repair",      repair_node,      next_step="execute"),
    PipelineStep("report",      report_node,      next_step="validate"),
    PipelineStep("validate",    validate_node,    next_step=None),  # None → END
]


def build_workflow() -> object:
    """从 PIPELINE_STEPS 配置列表构建 LangGraph 状态机"""
    workflow = StateGraph(dict)

    # 注册所有节点
    for step in PIPELINE_STEPS:
        workflow.add_node(step.name, step.node_func)

    # 连接边
    for step in PIPELINE_STEPS:
        if step.is_entry:
            workflow.set_entry_point(step.name)

        if step.conditional:
            cond_func, mapping = step.conditional
            workflow.add_conditional_edges(step.name, cond_func, mapping)
        elif step.next_step:
            workflow.add_edge(step.name, step.next_step)
        else:
            workflow.add_edge(step.name, END)

    return workflow.compile()


def run_workflow(initial_state: dict, callbacks: dict | None = None) -> dict:
    """执行工作流"""
    workflow = build_workflow()
    if callbacks:
        initial_state["_callbacks"] = callbacks
    final_state = workflow.invoke(initial_state)
    return final_state