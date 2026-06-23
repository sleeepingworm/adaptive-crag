"""
工作流相关数据结构：GraphState, TaskPlan, TaskType, CodePlan
"""

from dataclasses import dataclass, field
from enum import Enum


class TaskType(str, Enum):
    LITERATURE_SEARCH = "literature_search"
    DATA_ANALYSIS = "data_analysis"
    HYBRID = "hybrid"


@dataclass
class TaskPlan:
    """任务规划"""
    original_query: str = ""
    sub_tasks: list[dict] = field(default_factory=list)
    requires_code: bool = False
    requires_web_search: bool = False
    output_format: str = "markdown"

    def to_dict(self) -> dict:
        return {
            "original_query": self.original_query,
            "sub_tasks": self.sub_tasks,
            "requires_code": self.requires_code,
            "requires_web_search": self.requires_web_search,
            "output_format": self.output_format,
        }


@dataclass
class CodePlan:
    """代码方案说明"""
    plan_description: str = ""
    code_plan: str = ""
    variables: list[dict] = field(default_factory=list)


@dataclass
class GraphState:
    """LangGraph 工作流状态"""
    # 输入
    query: str = ""
    uploaded_files: list[str] = field(default_factory=list)

    # 任务计划
    plan: dict | None = None  # TaskPlan 的 dict 形态

    # 检索
    retrieved_chunks: list = field(default_factory=list)
    web_search_results: list = field(default_factory=list)
    evidence_ready: bool = False
    evidence_gap: str | None = None

    # 代码生成与执行
    code: str | None = None
    code_plan: str | None = None
    execution_result: dict | None = None
    execution_error: str | None = None
    retry_count: int = 0
    max_retries: int = 3

    # 报告
    report: str | None = None
    report_ready: bool = False
    citations_valid: bool = False

    # 控制字段
    current_step: str = "init"
    errors: list[str] = field(default_factory=list)
    completed: bool = False
