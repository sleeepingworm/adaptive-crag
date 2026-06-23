"""
adaptive_crag.ingestion - 文件解析与索引
========================================
读取 PDF/TXT/MD/CSV/Excel 文件，清洗文本，切片，
并对表格数据做字段分析和摘要。
"""

from .document_loader import load_document
from .text_cleaner import clean_text, clean_pdf_page_text
from .chunker import chunk_by_paragraph, chunk_by_heading, chunk_pdf
from .citation_mapper import PageMapping, build_page_mapping
from .dataset_profiler import profile_csv, profile_excel


class IngestionPipeline:
    """文件解析流水线，一次处理一个文件。"""

    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens

    def process(self, file_path: str) -> dict:
        """
        完整流水线：
        1. 检测文件类型
        2. load_document -> raw_text
        3. clean_text
        4. chunk（按类型选择策略）
        5. build_page_mapping
        6. 对 CSV/Excel 做 profile
        7. 返回结果 dict
        """
        from adaptive_crag.schema import DocumentType

        # 检测文件类型
        doc_type = self._detect_type(file_path)

        # 对 CSV/Excel 做数据集分析
        profile = None
        if doc_type in (DocumentType.CSV, DocumentType.EXCEL):
            try:
                if doc_type == DocumentType.CSV:
                    profile = profile_csv(file_path)
                else:
                    profile = profile_excel(file_path)
            except Exception:
                pass  # profile 失败不阻止主流程

        # 加载文档
        document, raw_text = load_document(file_path)

        # 清洗文本
        cleaned = clean_text(raw_text, doc_type.value)

        # 切片
        if doc_type in (DocumentType.CSV, DocumentType.EXCEL):
            chunks = []
        elif doc_type == DocumentType.MARKDOWN:
            chunks = chunk_by_heading(cleaned, document.doc_id, self.max_tokens)
        elif doc_type == DocumentType.PDF:
            chunks = chunk_pdf(file_path, document.doc_id, self.max_tokens)
        else:
            chunks = chunk_by_paragraph(cleaned, document.doc_id, self.max_tokens)

        # 页码映射
        pages = build_page_mapping(chunks, raw_text)

        document.chunk_count = len(chunks)

        return {
            "document": document,
            "chunks": chunks,
            "pages": pages,
            "profile": profile,
        }

    def _detect_type(self, file_path: str) -> "DocumentType":
        """根据扩展名检测文档类型"""
        from adaptive_crag.schema import DocumentType

        ext = file_path.lower().split(".")[-1] if "." in file_path else ""
        mapping = {
            "pdf": DocumentType.PDF,
            "txt": DocumentType.TXT,
            "md": DocumentType.MARKDOWN,
            "markdown": DocumentType.MARKDOWN,
            "csv": DocumentType.CSV,
            "xls": DocumentType.EXCEL,
            "xlsx": DocumentType.EXCEL,
        }
        return mapping.get(ext, DocumentType.TXT)


__all__ = ["IngestionPipeline", "load_document", "clean_text", "chunk_by_paragraph",
           "chunk_by_heading", "chunk_pdf", "build_page_mapping",
           "profile_csv", "profile_excel"]
