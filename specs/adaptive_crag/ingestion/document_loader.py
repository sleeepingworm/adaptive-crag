"""
文档加载器：读取 PDF/TXT/Markdown 文件为原始文本。
"""

import hashlib
import os

from adaptive_crag.schema import Document, DocumentType


def load_document(file_path: str) -> tuple[Document, str]:
    """
    读取文件返回 Document 元信息和原始文本。

    支持格式: .pdf, .txt, .md
    PDF 使用 PyMuPDF (fitz) 解析
    TXT/MD 使用 UTF-8 编码读取

    返回: (Document, raw_text)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_size = os.path.getsize(file_path)
    filename = os.path.basename(file_path)
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    # 计算文件 hash
    file_hash = _compute_hash(file_path)

    doc_type = _ext_to_doc_type(ext)
    raw_text = ""

    if doc_type == DocumentType.PDF:
        raw_text, page_count = _load_pdf(file_path)
        doc = Document.create(
            filename=filename, file_path=file_path,
            doc_type=doc_type, file_size_bytes=file_size,
            file_hash=file_hash, page_count=page_count,
        )
    else:
        raw_text = _load_text(file_path)
        doc = Document.create(
            filename=filename, file_path=file_path,
            doc_type=doc_type, file_size_bytes=file_size,
            file_hash=file_hash,
        )

    return doc, raw_text


def _compute_hash(file_path: str) -> str:
    """计算文件的 SHA256 哈希"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()


def _ext_to_doc_type(ext: str) -> DocumentType:
    mapping = {
        "pdf": DocumentType.PDF,
        "txt": DocumentType.TXT,
        "md": DocumentType.MARKDOWN,
        "markdown": DocumentType.MARKDOWN,
    }
    return mapping.get(ext, DocumentType.TXT)


def _load_text(file_path: str) -> str:
    """读取文本文件（UTF-8）"""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _load_pdf(file_path: str) -> tuple[str, int]:
    """使用 PyMuPDF 解析 PDF 文件"""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("需要安装 PyMuPDF: pip install PyMuPDF")

    doc = fitz.open(file_path)
    texts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        texts.append(text)
    doc.close()

    raw_text = "\n\n".join(texts)
    return raw_text, len(texts)
