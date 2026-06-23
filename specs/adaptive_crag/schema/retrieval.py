"""
检索相关数据结构：SearchResult, EvidenceSet
"""

from dataclasses import dataclass, field


@dataclass
class SearchResult:
    """单条检索结果"""
    chunk_id: str
    text: str
    score: float = 0.0
    rerank_score: float | None = None
    page_num: int | None = None
    doc_id: str = ""
    filename: str = ""
    hit_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "score": self.score,
            "rerank_score": self.rerank_score,
            "page_num": self.page_num,
            "doc_id": self.doc_id,
            "filename": self.filename,
            "hit_reason": self.hit_reason,
        }


@dataclass
class EvidenceSet:
    """证据集合"""
    query: str = ""
    results: list[SearchResult] = field(default_factory=list)
    total_found: int = 0
    source: str = "hybrid"  # hybrid | vector | bm25

    def to_dict(self) -> dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "total_found": self.total_found,
            "source": self.source,
        }

    @property
    def is_empty(self) -> bool:
        return len(self.results) == 0
