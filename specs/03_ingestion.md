# 模块说明书：文件解析与索引 (ingestion)

## 所属层级
数据与产物层

## 目标目录
`adaptive_crag/ingestion/`

生成文件：
```
adaptive_crag/ingestion/
    __init__.py             # 导出 IngestionPipeline
    document_loader.py      # 文档读取器
    text_cleaner.py         # 文本清洗
    chunker.py              # 文本切片
    citation_mapper.py      # 页码映射
    dataset_profiler.py     # 表格数据摘要
```

## 依赖模块

- **必须先生成**：`01_schema`（使用 Document, Chunk, DatasetProfile, DocumentType, ChunkStrategy）
- **可选**：`02_config`（使用 RetrievalConfig 中的切片参数）

## 职责边界

**做：**
- 读取 PDF、TXT、Markdown 文件为原始文本
- 清洗文本（去除页眉页脚、乱码、多余空白）
- 按语义边界和 token 阈值将文本切块
- 保留每个 chunk 对应的原文页码（PDF）或位置索引
- 对 CSV/Excel 做字段分析和数据摘要
- 将结果输出为 schema 中定义的结构

**不做：**
- 不做向量化（交给 retrieval 模块）
- 不要做关键词索引
- 不要做网络请求
- 不要调用 LLM

## 核心接口

### document_loader.py

```python
def load_document(file_path: str) -> tuple[Document, str]:
    """
    读取文件返回 Document 元信息和原始文本。

    输入: file_path - 文件绝对路径
    输出: (Document, raw_text)
    支持格式: .pdf, .txt, .md
    PDF 使用 PyMuPDF (fitz) 解析
    TXT/MD 使用 UTF-8 编码读取
    """
```

### text_cleaner.py

```python
def clean_text(raw_text: str, doc_type: str) -> str:
    """
    清洗文本。
    - 去除连续空行（保留单空行分段）
    - 去除页眉页脚（重复出现在每页的短行）
    - 去除不可见字符
    - 统一换行符为 \\n
    不改变语义内容。
    """

def clean_pdf_page_text(page_text: str) -> str:
    """
    对单页 PDF 文本做精细清洗。
    - 去除页码行
    - 去除页眉/页脚（基于位置和重复模式）
    """
```

### chunker.py

```python
def chunk_by_paragraph(cleaned_text: str, doc_id: str, max_tokens: int = 512) -> list[Chunk]:
    """
    按段落切片，段落过长时进一步按 token 拆分。
    返回 Chunk 列表，每个 chunk 保留段落索引。
    """

def chunk_by_heading(cleaned_text: str, doc_id: str, max_tokens: int = 512) -> list[Chunk]:
    """
    按 Markdown 标题切片（适合 .md 文件）。
    每个标题及其内容为一个 chunk。
    """

def chunk_pdf(pdf_path: str, doc_id: str, max_tokens: int = 512) -> list[Chunk]:
    """
    专门处理 PDF：逐页解析 -> 逐页清洗 -> 按页切片。
    每页一个或多个 chunk，每个 chunk 携带 page_num。
    返回 Chunk 列表。
    """
```

### citation_mapper.py

```python
@dataclass
class PageMapping:
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
```

### dataset_profiler.py

```python
def profile_csv(csv_path: str) -> DatasetProfile:
    """
    分析 CSV 文件：
    - 行数、列数
    - 每列名称、类型、缺失值数量
    - 前 5 行样例
    返回 DatasetProfile。
    """

def profile_excel(excel_path: str, sheet_name: str | None = None) -> DatasetProfile:
    """
    分析 Excel 文件，同上。
    默认读取第一个 sheet。
    """
```

### __init__.py 导出的主入口

```python
class IngestionPipeline:
    """
    文件解析流水线。一次处理一个文件。

    用法:
        pipeline = IngestionPipeline(max_tokens=512)
        result = pipeline.process("path/to/file.pdf")
        # result == {"document": Document, "chunks": list[Chunk], "profile": DatasetProfile | None}
    """

    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens
        self.chunker = Chunker(max_tokens)

    def process(self, file_path: str) -> dict:
        """
        完整流水线:
        1. 检测文件类型
        2. load_document -> raw_text
        3. clean_text
        4. chunk（按类型选择策略）
        5. build_page_mapping
        6. 对 CSV/Excel 做 profile
        7. 返回 {"document": Document, "chunks": list[Chunk], "pages": list[PageMapping], "profile": DatasetProfile | None}
        """
```

## 实现约束

1. **PDF 解析依赖**：使用 `PyMuPDF` (fitz) 或 `pdfplumber`
2. **编码处理**：所有文本读取用 UTF-8，遇到无法解码的字符用 `errors="replace"`
3. **大文件**：超过 100 页的 PDF 应分批处理，不一次性加载入内存
4. **切片不可跨页**：PDF 的 chunk 不能跨 page_num
5. **特殊字符**：不可见字符 `\x00-\x08` 等必须去除
6. **页码映射精度**：至少保留 chunk 在原文中的 start_char 和 end_char

## 与上下游模块的对接

- **上游调用方**：页面交互层（用户上传文件时调用）
- **上游调用方**：应用编排层（任务开始时批量处理文件）
- **下游消费方**：`retrieval` 模块消费 `Chunk` 列表建立索引
- **数据流向**：`file_path -> IngestionPipeline.process() -> {Document, Chunk[], PageMapping[], DatasetProfile?}`

## 测试要点

- 加载一个 3 页 PDF，能正确返回 3 个以上的 chunk
- 每个 chunk 带有正确的 page_num
- TXT 文件切片后 chunk 数量符合预期
- CSV 文件能正确生成 DatasetProfile
- 清洗能去除常见页眉页脚模式
- 超大 token 的段落能被正确拆分
- 不含文字的 PDF 返回空 chunk 列表（不崩溃）