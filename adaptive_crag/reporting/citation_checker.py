"""
引用校验器：检查报告中的关键结论是否能反查到来源。
"""

import re


class CitationChecker:
    """
    引用校验器。检查报告中的关键结论是否能反查到具体的 Chunk。
    """

    def __init__(self, citation_mappings: dict[str, dict] | None = None):
        """
        citation_mappings: {chunk_id: {doc_id, page_num, filename, text_snippet}}
        """
        self.citation_mappings = citation_mappings or {}

    def check_report(self, report: str, citations: list[dict]) -> dict:
        """
        检查报告中的所有引用。

        同时交叉校验：
        - 引用列表中每条是否可反查
        - 报告正文中的 [N] 脚注是否对应有效的引用条目

        返回:
        {
            "valid": bool,
            "total_citations": int,
            "valid_citations": int,
            "invalid_citations": list[dict],
            "unverified_claims": list[dict],
            "orphan_footnotes": list[str],
        }
        """
        invalid = []
        valid_count = 0

        for cit in citations:
            if self.check_citation(cit):
                valid_count += 1
            else:
                invalid.append({
                    "citation_id": cit.get("citation_id", ""),
                    "claim": cit.get("claim", "")[:100],
                    "reason": self._get_invalid_reason(cit),
                })

        # 交叉校验：报告中的 [N] 脚注是否超出引用列表范围
        orphan_footnotes = self._find_orphan_footnotes(report, len(citations))

        return {
            "valid": len(invalid) == 0 and len(orphan_footnotes) == 0,
            "total_citations": len(citations),
            "valid_citations": valid_count,
            "invalid_citations": invalid,
            "unverified_claims": self._find_unverified_claims(report),
            "orphan_footnotes": orphan_footnotes,
        }

    def check_citation(self, citation: dict) -> bool:
        """检查单条引用是否能反查"""
        chunk_id = citation.get("chunk_id", "")
        if not chunk_id:
            return False
        if chunk_id not in self.citation_mappings:
            return False

        mapping = self.citation_mappings[chunk_id]
        doc_id = citation.get("source_doc_id", "")
        if doc_id and mapping.get("doc_id") != doc_id:
            return False

        return True

    def _get_invalid_reason(self, citation: dict) -> str:
        """获取引用无效的原因"""
        chunk_id = citation.get("chunk_id", "")
        if not chunk_id:
            return "引用缺少 chunk_id"
        if chunk_id not in self.citation_mappings:
            return f"chunk_id {chunk_id} 不存在于引用映射中"
        return "doc_id 不匹配"

    def _find_orphan_footnotes(self, report: str, citation_count: int) -> list[str]:
        """查找报告中 [N] 脚注编号超过引用列表长度的孤立脚注"""
        if citation_count == 0:
            return []
        footnotes = re.findall(r'\[(\d+)\]', report)
        orphan = [f"[{fn}]" for fn in footnotes if int(fn) > citation_count]
        return list(set(orphan))

    def _find_unverified_claims(self, report: str) -> list[dict]:
        """查找报告中没有引用标注的结论段落"""
        if not report:
            return []
        paragraphs = re.split(r"\n\s*\n", report)
        unverified = []
        for para in paragraphs:
            if len(para) > 50 and not re.search(r"\[\d+\]", para):
                if not para.startswith("#") and not para.startswith("!"):
                    unverified.append({
                        "claim": para[:100],
                        "reason": "无引用标注",
                    })
        # 最多返回 10 条，避免报告过长
        return unverified[:10]
