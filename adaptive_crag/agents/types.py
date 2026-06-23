"""
Agent 接口契约类型定义。
每个 Agent 的输入输出从此有明确的类型，不再用裸 dict 通信。
"""

from dataclasses import dataclass, field


# ========== RouterAgent ==========

@dataclass
class RouterInput:
    """RouterAgent 需要的状态信息"""
    query: str = ""
    uploaded_files: list[str] = field(default_factory=list)


@dataclass
class RouterOutput:
    """RouterAgent 返回的任务计划"""
    plan: dict = field(default_factory=dict)
    requires_code: bool = False
    requires_web_search: bool = False


# ========== GraderAgent ==========

@dataclass
class GraderInput:
    """GraderAgent 需要的状态信息"""
    query: str = ""
    retrieved_chunks: list[dict] = field(default_factory=list)
    web_search_results: list[dict] = field(default_factory=list)
    evidence_gap: str | None = None


@dataclass
class GraderOutput:
    """GraderAgent 返回的证据评估"""
    evidence_ready: bool = False
    evidence_gap: str | None = None
    confidence: float = 0.0


# ========== AnalyzerAgent ==========

@dataclass
class AnalyzerInput:
    """AnalyzerAgent 需要的状态信息"""
    query: str = ""
    plan: dict = field(default_factory=dict)
    retrieved_chunks: list[dict] = field(default_factory=list)


@dataclass
class AnalyzerOutput:
    """AnalyzerAgent 返回的分析方案"""
    code_plan: str = ""
    plan_description: str = ""
    variables: list[str] = field(default_factory=list)


# ========== RepairAgent ==========

@dataclass
class RepairInput:
    """RepairAgent 需要的状态信息"""
    code: str = ""
    code_plan: str = ""
    execution_error: str = ""


@dataclass
class RepairOutput:
    """RepairAgent 返回的修复后代码"""
    code: str = ""


# ========== ReportAgent ==========

@dataclass
class ReportInput:
    """ReportAgent 需要的状态信息"""
    query: str = ""
    plan: dict = field(default_factory=dict)
    retrieved_chunks: list[dict] = field(default_factory=list)
    execution_result: dict | None = None
    web_search_results: list[dict] = field(default_factory=list)


@dataclass
class ReportOutput:
    """ReportAgent 返回的报告"""
    report: str = ""
    report_ready: bool = False


# ========== ValidatorAgent ==========

@dataclass
class ValidatorInput:
    """ValidatorAgent 需要的状态信息"""
    report: str = ""
    citations: list[dict] = field(default_factory=list)


@dataclass
class ValidatorOutput:
    """ValidatorAgent 返回的校验结果"""
    citations_valid: bool = False
    issues: list[dict] = field(default_factory=list)