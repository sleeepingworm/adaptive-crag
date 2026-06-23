"""
报告构建器：将报告内容、引用、图表打包为 ReportBundle。
"""

import os
import json
from datetime import datetime
from adaptive_crag.schema import ReportBundle


class ReportBuilder:
    """
    报告构建器。整合报告正文、引用映射、图表索引、证据包。
    """

    def __init__(self, artifact_manager=None):
        self.artifact_manager = artifact_manager

    def build(
        self,
        query: str,
        report_markdown: str,
        evidence_set: dict | None = None,
        execution_artifact: dict | None = None,
        citations: list[dict] | None = None,
        chart_paths: list[str] | None = None,
        log_paths: list[str] | None = None,
        task_id: str = "",
    ) -> ReportBundle:
        """
        构造完整的 ReportBundle。
        """
        citations = citations or []
        chart_paths = chart_paths or []
        log_paths = log_paths or []

        # 格式化引用脚注
        formatted_citations = self._format_citations(citations)

        # 将引用插入报告
        report = report_markdown
        if formatted_citations:
            report = report + "\n\n---\n" + formatted_citations

        # 嵌入图表
        if chart_paths and self.artifact_manager:
            artifact_dir = getattr(self.artifact_manager, "artifact_dir", "")
            if artifact_dir:
                report = self._embed_charts(report, chart_paths, artifact_dir)

        return ReportBundle(
            task_id=task_id,
            query=query,
            report_markdown=report,
            citations=citations,
            chart_paths=chart_paths,
            log_paths=log_paths,
            generated_at=datetime.now().isoformat(),
        )

    def _format_citations(self, citations: list[dict]) -> str:
        """将引用列表格式化为可读的引用脚注"""
        if not citations:
            return ""

        lines = ["## 引用列表\n"]
        for i, cit in enumerate(citations, 1):
            source = cit.get("source_filename", cit.get("source_doc_id", "未知来源"))
            page = cit.get("page_num")
            page_str = f"，第 {page} 页" if page else ""
            claim = cit.get("claim", "")[:80]
            lines.append(f"[{i}] {source}{page_str} — {claim}")

        return "\n".join(lines)

    def _embed_charts(self, report: str, chart_paths: list[str],
                      artifact_dir: str) -> str:
        """将图表路径嵌入 Markdown。"""
        if not chart_paths:
            return report

        chart_section = "\n\n## 数据图表\n\n"
        for path in chart_paths:
            # 转为相对路径
            try:
                rel_path = os.path.relpath(path, artifact_dir)
            except ValueError:
                rel_path = path
            chart_section += f"![]({rel_path})\n\n"

        # 在报告末尾插入图表
        return report + chart_section
