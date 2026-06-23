"""
文本切片工具：按段落、标题或 PDF 页面进行切片。
"""

import re
from adaptive_crag.schema import Chunk, ChunkStrategy


def chunk_by_paragraph(cleaned_text: str, doc_id: str, max_tokens: int = 512) -> list[Chunk]:
    """
    按段落切片，段落过长时进一步按 token 拆分。
    返回 Chunk 列表，每个 chunk 保留段落索引。
    """
    # 按空行分割段落
    paragraphs = re.split(r"\n\s*\n", cleaned_text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    for idx, para in enumerate(paragraphs):
        token_count = _estimate_tokens(para)

        if token_count <= max_tokens:
            chunks.append(Chunk.create(
                doc_id=doc_id,
                text=para,
                strategy=ChunkStrategy.PARAGRAPH,
                paragraph_idx=idx,
                token_count=token_count,
            ))
        else:
            # 过长段落按句子拆分
            sub_chunks = _split_long_paragraph(para, doc_id, idx, max_tokens)
            chunks.extend(sub_chunks)

    return chunks


def chunk_by_heading(cleaned_text: str, doc_id: str, max_tokens: int = 512) -> list[Chunk]:
    """
    按 Markdown 标题切片（适合 .md 文件）。
    每个标题及其内容为一个 chunk。
    """
    # 匹配 Markdown 标题
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    splits = list(heading_pattern.finditer(cleaned_text))

    chunks = []
    if not splits:
        # 没有标题时按段落切片
        return chunk_by_paragraph(cleaned_text, doc_id, max_tokens)

    for i, match in enumerate(splits):
        start = match.start()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(cleaned_text)
        section_text = cleaned_text[start:end].strip()
        heading_text = match.group(2).strip()

        token_count = _estimate_tokens(section_text)
        if token_count <= max_tokens:
            chunks.append(Chunk.create(
                doc_id=doc_id,
                text=section_text,
                strategy=ChunkStrategy.HEADING,
                heading=heading_text,
                paragraph_idx=i,
                token_count=token_count,
            ))
        else:
            sub_chunks = _split_long_paragraph(
                section_text, doc_id, i, max_tokens, heading=heading_text
            )
            chunks.extend(sub_chunks)

    return chunks


def chunk_pdf(pdf_path: str, doc_id: str, max_tokens: int = 512) -> list[Chunk]:
    """
    专门处理 PDF：逐页解析 -> 逐页清洗 -> 按页切片。
    每页一个或多个 chunk，每个 chunk 携带 page_num。
    返回 Chunk 列表。
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")

    from .text_cleaner import clean_pdf_page_text

    doc = fitz.open(pdf_path)
    chunks = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        cleaned = clean_pdf_page_text(page_text)
        cleaned = cleaned.strip()

        if not cleaned:
            continue

        token_count = _estimate_tokens(cleaned)
        if token_count <= max_tokens:
            chunks.append(Chunk.create(
                doc_id=doc_id,
                text=cleaned,
                strategy=ChunkStrategy.PARAGRAPH,
                page_num=page_num + 1,
                token_count=token_count,
            ))
        else:
            # 超过一页的内容按段落拆分
            paragraphs = re.split(r"\n\s*\n", cleaned)
            for p_idx, para in enumerate(paragraphs):
                para = para.strip()
                if not para:
                    continue
                ptokens = _estimate_tokens(para)
                if ptokens <= max_tokens:
                    chunks.append(Chunk.create(
                        doc_id=doc_id,
                        text=para,
                        strategy=ChunkStrategy.PARAGRAPH,
                        page_num=page_num + 1,
                        paragraph_idx=p_idx,
                        token_count=ptokens,
                    ))
                else:
                    # 极长段落再拆分
                    sub_chunks = _split_long_paragraph(
                        para, doc_id, p_idx, max_tokens, page_num=page_num + 1
                    )
                    chunks.extend(sub_chunks)

    doc.close()
    return chunks


def _split_long_paragraph(text: str, doc_id: str, para_idx: int,
                          max_tokens: int, heading: str | None = None,
                          page_num: int | None = None) -> list[Chunk]:
    """将过长段落按句子拆分"""
    # 按中文句号、问号、感叹号、换行拆分
    sentences = re.split(r"(?<=[。！？.!?\n])\s*", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_text = ""
    current_tokens = 0
    sub_idx = 0

    for sent in sentences:
        sent_tokens = _estimate_tokens(sent)
        if current_tokens + sent_tokens > max_tokens and current_text:
            chunks.append(Chunk.create(
                doc_id=doc_id,
                text=current_text.strip(),
                strategy=ChunkStrategy.PARAGRAPH,
                page_num=page_num,
                paragraph_idx=para_idx,
                heading=heading,
                token_count=current_tokens,
            ))
            current_text = sent
            current_tokens = sent_tokens
            sub_idx += 1
        else:
            current_text += sent + " "
            current_tokens += sent_tokens

    if current_text.strip():
        chunks.append(Chunk.create(
            doc_id=doc_id,
            text=current_text.strip(),
            strategy=ChunkStrategy.PARAGRAPH,
            page_num=page_num,
            paragraph_idx=para_idx,
            heading=heading,
            token_count=current_tokens,
        ))

    return chunks


def _estimate_tokens(text: str) -> int:
    """粗略估算 token 数"""
    return max(1, int(len(text) / 1.5))
