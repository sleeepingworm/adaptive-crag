"""
产物管理：管理任务产物目录结构和索引。
"""

import os
import json
from datetime import datetime


class ArtifactManager:
    """
    管理一次任务的产物目录结构和产物索引。
    """

    def __init__(self, root_artifact_dir: str, task_id: str):
        self.root_artifact_dir = root_artifact_dir
        self.task_id = task_id
        self.artifact_dir = os.path.join(root_artifact_dir, task_id)

    def ensure_dirs(self) -> str:
        """创建产物目录结构"""
        dirs = [
            os.path.join(self.artifact_dir, "charts"),
            os.path.join(self.artifact_dir, "data"),
            os.path.join(self.artifact_dir, "logs"),
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        return self.artifact_dir

    def save_report(self, report_md: str) -> str:
        """保存 Markdown 报告"""
        report_path = os.path.join(self.artifact_dir, "report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        return report_path

    def save_citations(self, citations: list[dict]) -> str:
        """保存引用映射为 JSON"""
        path = os.path.join(self.artifact_dir, "citations.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(citations, f, ensure_ascii=False, indent=2)
        return path

    def save_event_log(self, event: dict) -> None:
        """追加记录一条事件日志"""
        import json
        log_path = os.path.join(self.artifact_dir, "logs", "event_log.jsonl")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def collect_charts(self) -> list[str]:
        """扫描 charts/ 目录，返回所有图片路径"""
        charts_dir = os.path.join(self.artifact_dir, "charts")
        if not os.path.exists(charts_dir):
            return []
        chart_paths = []
        for fname in os.listdir(charts_dir):
            ext = fname.lower().split(".")[-1] if "." in fname else ""
            if ext in ("png", "jpg", "jpeg", "svg", "pdf"):
                chart_paths.append(os.path.join(charts_dir, fname))
        return chart_paths

    def build_report_bundle(self, report_md: str, citations: list[dict]):
        """构造 ReportBundle 对象"""
        from adaptive_crag.schema import ReportBundle
        return ReportBundle(
            task_id=self.task_id,
            report_markdown=report_md,
            citations=citations,
            chart_paths=self.collect_charts(),
            log_paths=[os.path.join(self.artifact_dir, "logs", "event_log.jsonl")],
            generated_at=datetime.now().isoformat(),
        )
