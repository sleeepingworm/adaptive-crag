"""
评测相关数据结构：BenchmarkCase, BenchmarkResult
"""

from dataclasses import dataclass, field


@dataclass
class BenchmarkCase:
    """单个测试用例"""
    case_id: str = ""
    question: str = ""
    expected_evidence: list[str] = field(default_factory=list)
    expected_sources: list[str] = field(default_factory=list)
    category: str = "literature"
    scoring_rules: dict = field(default_factory=dict)
    setup_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "question": self.question,
            "expected_evidence": self.expected_evidence,
            "expected_sources": self.expected_sources,
            "category": self.category,
            "scoring_rules": self.scoring_rules,
            "setup_files": self.setup_files,
        }


@dataclass
class BenchmarkResult:
    """单个测试用例的评测结果"""
    case_id: str = ""
    question: str = ""
    system_type: str = ""
    success: bool = False
    total_time_ms: int = 0
    token_count: int = 0
    evidence_hit: bool = False
    citation_accuracy: float = 0.0
    retry_count: int = 0
    output: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "question": self.question,
            "system_type": self.system_type,
            "success": self.success,
            "total_time_ms": self.total_time_ms,
            "token_count": self.token_count,
            "evidence_hit": self.evidence_hit,
            "citation_accuracy": self.citation_accuracy,
            "retry_count": self.retry_count,
            "output": self.output,
            "errors": self.errors,
        }
