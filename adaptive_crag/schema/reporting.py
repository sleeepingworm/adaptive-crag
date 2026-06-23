"""
报告相关数据结构：Citation, ReportBundle
"""

from dataclasses import dataclass, field


@dataclass
class Citation:
    """单条引用"""
    citation_id: str
    claim: str = ""
    source_doc_id: str = ""
    source_filename: str = ""
    page_num: int | None = None
    chunk_id: str = ""
    source_type: str = "local_literature"
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "citation_id": self.citation_id,
            "claim": self.claim,
            "source_doc_id": self.source_doc_id,
            "source_filename": self.source_filename,
            "page_num": self.page_num,
            "chunk_id": self.chunk_id,
            "source_type": self.source_type,
            "confidence": self.confidence,
        }


@dataclass
class ReportBundle:
    """完整报告包"""
    task_id: str = ""
    query: str = ""
    report_markdown: str = ""
    citations: list[dict] = field(default_factory=list)
    chart_paths: list[str] = field(default_factory=list)
    log_paths: list[str] = field(default_factory=list)
    generated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "query": self.query,
            "report_markdown": self.report_markdown,
            "citations": self.citations,
            "chart_paths": self.chart_paths,
            "log_paths": self.log_paths,
            "generated_at": self.generated_at,
        }
