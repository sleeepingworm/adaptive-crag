"""
adaptive_crag.agents - Agent 能力封装
=====================================
每个 Agent 封装 LLM 调用逻辑，构造 prompt，解析结构化响应。
"""

from .base_agent import BaseAgent
from .router_agent import RouterAgent
from .grader_agent import GraderAgent
from .analyzer_agent import AnalyzerAgent
from .repair_agent import RepairAgent
from .report_agent import ReportAgent
from .validator_agent import ValidatorAgent
from .prompts import (
    ROUTER_SYSTEM_PROMPT,
    GRADER_SYSTEM_PROMPT,
    ANALYZER_SYSTEM_PROMPT,
    REPAIR_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    VALIDATOR_SYSTEM_PROMPT,
)

__all__ = [
    "BaseAgent",
    "RouterAgent",
    "GraderAgent",
    "AnalyzerAgent",
    "RepairAgent",
    "ReportAgent",
    "ValidatorAgent",
    # prompts
    "ROUTER_SYSTEM_PROMPT",
    "GRADER_SYSTEM_PROMPT",
    "ANALYZER_SYSTEM_PROMPT",
    "REPAIR_SYSTEM_PROMPT",
    "REPORT_SYSTEM_PROMPT",
    "VALIDATOR_SYSTEM_PROMPT",
]
