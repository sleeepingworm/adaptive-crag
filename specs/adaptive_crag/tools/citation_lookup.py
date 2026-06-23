"""
引用反查工具。供 Report Agent 和 Citation Validator 调用。
"""

# 全局引用映射（从 ingestion 初始化）
_citation_mappings: dict[str, dict] = {}


def set_citation_mappings(mappings: dict[str, dict]):
    """设置引用映射"""
    global _citation_mappings
    _citation_mappings = mappings


def citation_lookup(params: dict) -> dict:
    """
    引用反查工具。

    params:
        chunk_id: str
        doc_id: str | None = None
    """
    chunk_id = params.get("chunk_id", "")
    doc_id = params.get("doc_id")

    if not chunk_id:
        return {"success": False, "result": None, "error": "chunk_id 不能为空"}

    mapping = _citation_mappings.get(chunk_id)
    if mapping is None:
        return {
            "success": False,
            "result": None,
            "error": f"chunk_id {chunk_id} 未找到",
        }

    if doc_id and mapping.get("doc_id") != doc_id:
        return {
            "success": False,
            "result": None,
            "error": f"doc_id 不匹配（期望 {doc_id}，实际 {mapping.get('doc_id')}）",
        }

    return {
        "success": True,
        "result": {
            "chunk_id": chunk_id,
            "doc_id": mapping.get("doc_id", ""),
            "filename": mapping.get("filename", ""),
            "page_num": mapping.get("page_num"),
            "text_snippet": mapping.get("text_snippet", "")[:200],
            "file_path": mapping.get("file_path", ""),
        },
    }
