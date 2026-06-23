"""
adaptive_crag.reporting - 报告与引用层
=====================================
报告构建、引用校验、Markdown 格式化。
"""

from .report_builder import ReportBuilder
from .citation_checker import CitationChecker
from .markdown_builder import MarkdownBuilder

__all__ = ["ReportBuilder", "CitationChecker", "MarkdownBuilder"]
