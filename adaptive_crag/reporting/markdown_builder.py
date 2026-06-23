"""
Markdown 格式化工具。不依赖 LLM，纯字符串操作。
"""

import re


class MarkdownBuilder:
    """Markdown 格式化工具"""

    @staticmethod
    def build_report(
        title: str,
        sections: list[dict],
        charts: list[str] | None = None,
        citations: list[dict] | None = None,
    ) -> str:
        """
        构建标准格式的 Markdown 报告。

        sections: [
            {"heading": "摘要", "content": "..."},
            {"heading": "核心结论", "content": "...", "citations": ["cite_001"]},
        ]
        """
        lines = [f"# {title}", ""]

        for section in sections:
            heading = section.get("heading", "")
            content = section.get("content", "")
            lines.append(f"## {heading}")
            lines.append("")
            lines.append(content)
            lines.append("")

        # 插入图表
        if charts:
            lines.append("## 数据图表")
            lines.append("")
            for chart in charts:
                lines.append(f"![]({chart})")
                lines.append("")

        # 插入引用
        if citations:
            lines.append("## 引用列表")
            lines.append("")
            for i, cit in enumerate(citations, 1):
                source = cit.get("source_filename", "未知")
                lines.append(f"[{i}] {source}")

        return "\n".join(lines)

    @staticmethod
    def insert_footnotes(report: str, citation_map: dict[str, str]) -> str:
        """
        将 report 中的 [cite_id] 替换为 [1][2] 脚注标记，
        并在文末添加脚注列表。

        只替换已知存在于 citation_map 中的 ID，避免误替换普通方括号内容。
        """
        result = report
        footnote_lines = ["\n\n---\n## 引用列表\n"]
        idx = 1
        id_to_num = {}

        # 只匹配已知在 citation_map 中的 cite_id
        known_ids = set(citation_map.keys())
        if not known_ids:
            return report + "\n".join(footnote_lines)

        def replace_cite(match):
            nonlocal idx
            cite_id = match.group(1)
            if cite_id not in known_ids:
                return match.group(0)  # 不替换未知 ID
            if cite_id not in id_to_num:
                id_to_num[cite_id] = idx
                source = citation_map.get(cite_id, cite_id)
                footnote_lines.append(f"[{idx}] {source}")
                idx += 1
            return f"[{id_to_num[cite_id]}]"

        result = re.sub(r'\[(' + '|'.join(re.escape(k) for k in known_ids) + r')\]', replace_cite, result)
        result += "\n".join(footnote_lines)
        return result

    @staticmethod
    def sanitize_markdown(text: str) -> str:
        """清理 LLM 输出中的异常 Markdown"""
        # 修复未闭合的加粗
        if text.count("**") % 2 != 0:
            text = text + "**"

        # 修复表格格式
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            # 处理被错误拆分的表格行
            if line.count("|") > 0 and "---" not in line:
                line = line.strip()
            cleaned.append(line)

        return "\n".join(cleaned)
