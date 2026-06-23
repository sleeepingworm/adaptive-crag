"""
文本切片工具：按段落、标题或 PDF 页面进行切片。
"""

import re
from adaptive_crag.schema import Chunk, ChunkStrategy
from adaptive_crag.schema.documents import estimate_tokens as _estimate_tokens


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

        # 提取该页表格，追加到文本末尾，让 LLM 能读到表格数据
        try:
            table_texts = _extract_page_tables(page)
            if table_texts:
                cleaned = cleaned + "\n\n" + "\n\n".join(table_texts) if cleaned else "\n\n".join(table_texts)
        except Exception:
            pass  # 表格提取失败不影响主流程

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


def _extract_page_tables(page) -> list[str]:
    """从 PyMuPDF 页面提取表格，格式化为可读文本列表"""
    try:
        tabs = page.find_tables()
    except Exception:
        return []
    if not tabs or not tabs.tables:
        return []

    texts = []
    for i, tab in enumerate(tabs.tables):
        try:
            rows = tab.extract()
        except Exception:
            continue
        if not rows:
            continue
        formatted = _format_table_for_text(rows, table_index=i + 1)
        if formatted:
            texts.append(formatted)
    return texts


def _format_table_for_text(rows: list, table_index: int = 1) -> str:
    """将表格行列转为可读文本"""
    if not rows:
        return ""

    # 过滤完全空行和纯 None 行
    clean_rows = []
    for row in rows:
        cells = [_cell_to_str(c) for c in row]
        if any(c.strip() for c in cells):
            clean_rows.append(cells)

    if not clean_rows:
        return ""

    lines = [f"[表 {table_index}]"]

    # 如果只有 1-2 行，用紧凑格式
    if len(clean_rows) <= 2:
        for cells in clean_rows:
            lines.append(" | ".join(cells))
    else:
        # 多行用表头+数据格式
        header = clean_rows[0]
        lines.append(" | ".join(header))
        lines.append(" | ".join("---" for _ in header))
        for cells in clean_rows[1:]:
            lines.append(" | ".join(cells))

    return "\n".join(lines)


def _cell_to_str(cell) -> str:
    """单元格转为字符串，处理 None 和换行"""
    if cell is None:
        return ""
    s = str(cell).replace("\n", " ").strip()
    return s


def merge_small_chunks(chunks: list[Chunk], min_tokens: int = 80, max_tokens: int = 512) -> list[Chunk]:
    """合并相邻的过小片段，避免标题和短段落被孤立。"""
    if not chunks:
        return chunks
    merged = []
    buf_text, buf_tokens, buf_heading, buf_page = "", 0, None, None
    buf_doc_id = chunks[0].doc_id
    buf_strategy = chunks[0].strategy

    def flush():
        nonlocal buf_text, buf_tokens, buf_heading
        if buf_text.strip():
            merged.append(Chunk.create(
                doc_id=buf_doc_id, text=buf_text.strip(), strategy=buf_strategy,
                heading=buf_heading, page_num=buf_page, token_count=buf_tokens))
        buf_text = ""; buf_tokens = 0; buf_heading = None

    for c in chunks:
        if c.heading and not buf_heading:
            buf_heading = c.heading
        if c.page_num and not buf_page:
            buf_page = c.page_num
        if buf_tokens + c.token_count <= max_tokens and buf_tokens < min_tokens:
            buf_text += "\n" + c.text if buf_text else c.text
            buf_tokens += c.token_count
        else:
            flush()
            buf_text = c.text; buf_tokens = c.token_count
            buf_heading = c.heading; buf_page = c.page_num
            buf_doc_id = c.doc_id; buf_strategy = c.strategy
    flush()
    return merged
