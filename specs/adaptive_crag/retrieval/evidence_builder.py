"""
证据集合构建：将排序后的搜索结果构造为结构化证据。
"""


def build_evidence(query: str, ranked_chunks: list[dict], source: str = "hybrid") -> dict:
    """
    将排序后的搜索结果构造成 EvidenceSet 的 dict 形态。

    输出结构:
    {
        "results": [
            {
                "chunk_id": str,
                "text": str,
                "score": float,
                "rerank_score": float | None,
                "page_num": int | None,
                "doc_id": str,
                "filename": str,
                "hit_reason": str
            }
        ],
        "total_found": int,
        "source": str
    }
    """
    results = []
    for item in ranked_chunks:
        metadata = item.get("metadata", {})
        text = item.get("text", "")
        chunk_id = item.get("chunk_id", "")

        result = {
            "chunk_id": chunk_id,
            "text": text[:500] + "..." if len(text) > 500 else text,
            "score": float(item.get("score", 0)),
            "rerank_score": float(item["rerank_score"]) if item.get("rerank_score") is not None else None,
            "page_num": _to_int_or_none(metadata.get("page_num") if metadata else None),
            "doc_id": metadata.get("doc_id", "") if metadata else item.get("doc_id", ""),
            "filename": metadata.get("filename", "") if metadata else item.get("filename", ""),
            "hit_reason": _generate_hit_reason(query, text),
        }
        results.append(result)

    return {
        "results": results,
        "total_found": len(results),
        "source": source,
    }


def _to_int_or_none(value) -> int | None:
    """安全转换为 int 或 None"""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _generate_hit_reason(query: str, text: str) -> str:
    """生成简短说明为什么匹配"""
    query_keywords = set(query.lower().split())
    text_lower = text.lower()
    matched = [kw for kw in query_keywords if kw in text_lower and len(kw) > 1]
    if matched:
        return f"包含关键词: {', '.join(matched[:3])}"
    return "语义相似匹配"
