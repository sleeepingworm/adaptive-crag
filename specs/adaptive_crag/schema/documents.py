"""
文档相关数据结构：Document, Chunk, DatasetProfile
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class DocumentType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    MARKDOWN = "markdown"
    CSV = "csv"
    EXCEL = "excel"


class ChunkStrategy(str, Enum):
    PARAGRAPH = "paragraph"
    FIXED_TOKEN = "fixed_token"
    HEADING = "heading"


@dataclass
class Document:
    """文档元信息"""
    doc_id: str
    filename: str
    file_path: str
    doc_type: DocumentType
    page_count: int | None = None
    file_size_bytes: int = 0
    file_hash: str = ""
    uploaded_at: datetime = field(default_factory=datetime.now)
    chunk_count: int = 0

    @classmethod
    def create(cls, filename: str, file_path: str, doc_type: DocumentType,
               file_size_bytes: int = 0, file_hash: str = "",
               page_count: int | None = None) -> "Document":
        """便捷构造方法，自动生成 doc_id"""
        return cls(
            doc_id=f"doc_{uuid.uuid4().hex[:12]}",
            filename=filename,
            file_path=file_path,
            doc_type=doc_type,
            page_count=page_count,
            file_size_bytes=file_size_bytes,
            file_hash=file_hash,
            uploaded_at=datetime.now(),
        )


@dataclass
class Chunk:
    """文档切块"""
    chunk_id: str
    doc_id: str
    text: str
    page_num: int | None = None
    paragraph_idx: int | None = None
    heading: str | None = None
    strategy: ChunkStrategy = ChunkStrategy.PARAGRAPH
    token_count: int = 0
    embedding: list[float] | None = None

    @classmethod
    def create(cls, doc_id: str, text: str, strategy: ChunkStrategy = ChunkStrategy.PARAGRAPH,
               page_num: int | None = None, paragraph_idx: int | None = None,
               heading: str | None = None, token_count: int = 0) -> "Chunk":
        """便捷构造方法，自动生成 chunk_id"""
        return cls(
            chunk_id=f"chunk_{uuid.uuid4().hex[:12]}",
            doc_id=doc_id,
            text=text,
            page_num=page_num,
            paragraph_idx=paragraph_idx,
            heading=heading,
            strategy=strategy,
            token_count=token_count or estimate_tokens(text),
        )


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数（中英文混合按 1.5 字符/token）"""
    return max(1, int(len(text) / 1.5))


@dataclass
class DatasetProfile:
    """数据集/表格摘要"""
    file_path: str
    filename: str
    row_count: int = 0
    column_count: int = 0
    columns: list[dict] = field(default_factory=list)
    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    has_header: bool = True
