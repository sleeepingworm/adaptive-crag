"""
页码映射：构建 chunk -> 原文定位的映射表。
"""

from dataclasses import dataclass, field
from adaptive_crag.schema import Chunk


@dataclass
class PageMapping:
    """Chunk 到原文的定位映射"""
    chunk_id: str
    doc_id: str
    page_num: int | None
    start_char: int
    end_char: int


def build_page_mapping(chunks: list[Chunk], raw_text: str) -> list[PageMapping]:
    """
    构建 chunk -> 原文定位的映射表。
    用于最终报告反查引用来源。
    """
    mappings = []
    for chunk in chunks:
        # 在原文中查找 chunk 文本位置
        start_pos = raw_text.find(chunk.text[:100])
        if start_pos == -1:
            # 尝试前 50 字符
            start_pos = raw_text.find(chunk.text[:50])
        if start_pos == -1:
            # 无法定位时跳过
            continue

        end_pos = start_pos + len(chunk.text)

        mappings.append(PageMapping(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            page_num=chunk.page_num,
            start_char=start_pos,
            end_char=min(end_pos, len(raw_text)),
        ))

    return mappings
