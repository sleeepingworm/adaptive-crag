# 模块说明书：共享数据结构 (schema)

## 所属层级
跨模块基础层（所有模块依赖此模块）

## 目标目录
`adaptive_crag/schema/`

生成文件：
```
adaptive_crag/schema/
    __init__.py          # 导出所有数据结构
    documents.py         # Document, Chunk, DatasetProfile
    retrieval.py         # SearchResult, EvidenceSet
    workflow.py          # GraphState, TaskPlan, CodePlan
    execution.py         # ExecutionArtifact
    reporting.py         # Citation, ReportBundle
    evaluation.py        # BenchmarkCase, BenchmarkResult
```

## 依赖模块
无。这是项目的基石，所有其他模块都依赖此模块。

## 职责边界

**做：**
- 定义所有跨模块共用的数据类的形状和类型注解
- 使用 Python dataclass 或 Pydantic BaseModel 定义数据结构
- 提供类型注解，使得其他模块能静态检查

**不做：**
- 不做任何业务逻辑
- 不读写文件
- 不调用任何外部库（除了 dataclasses / pydantic）
- 不做 embedding 或检索

## 数据结构定义（使用 Pydantic 或 dataclass）

### documents.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

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
    doc_id: str                    # 唯一 ID，用 uuid
    filename: str                  # 原始文件名
    file_path: str                 # 上传后的绝对路径
    doc_type: DocumentType         # 文档类型
    page_count: int | None         # PDF 页码数
    file_size_bytes: int
    file_hash: str                 # sha256
    uploaded_at: datetime
    chunk_count: int = 0

@dataclass
class Chunk:
    chunk_id: str                  # chunk_{uuid}
    doc_id: str                    # 所属文档
    text: str                      # 切块文本
    page_num: int | None           # 页码（PDF 专用）
    paragraph_idx: int | None      # 段落索引
    heading: str | None            # 所在标题
    strategy: ChunkStrategy        # 切片策略
    token_count: int               # 估算 token 数
    embedding: list[float] | None = None  # 嵌入向量（可选）

@dataclass
class DatasetProfile:
    file_path: str
    filename: str
    row_count: int
    column_count: int
    columns: list[dict]            # [{"name": "age", "dtype": "int64", "missing": 2, "sample": [25, 30, ...]}, ...]
    numeric_columns: list[str]
    categorical_columns: list[str]
    has_header: bool = True
```

### workflow.py

```python
from dataclasses import dataclass, field
from enum import Enum

class TaskType(str, Enum):
    LITERATURE_SEARCH = "literature_search"     # 文献检索
    DATA_ANALYSIS = "data_analysis"             # 数据分析
    HYBRID = "hybrid"                           # 混合任务

@dataclass
class TaskPlan:
    original_query: str                          # 用户原始问题
    sub_tasks: list[dict]                        # [{"type": TaskType, "description": "...", "files": [...]}]
    requires_code: bool                          # 是否需要生成代码
    requires_web_search: bool                    # 是否需要联网
    output_format: str = "markdown"              # 报告格式

@dataclass
class GraphState:
    # 输入
    query: str                                   # 用户问题
    uploaded_files: list[str]                    # 上传文件路径列表

    # 任务计划
    plan: TaskPlan | None = None

    # 检索
    retrieved_chunks: list = field(default_factory=list)   # Chunk 列表（可 JSON 序列化）
    web_search_results: list = field(default_factory=list) # Web 检索结果
    evidence_ready: bool = False                 # 证据是否足够
    evidence_gap: str | None = None              # 证据缺口描述

    # 代码生成与执行
    code: str | None = None                      # 生成的 Python 代码
    code_plan: str | None = None                 # 代码思路说明
    execution_result: dict | None = None         # ExecutionArtifact 的 dict 形态
    execution_error: str | None = None           # 最后一次错误摘要
    retry_count: int = 0                         # 当前重试次数
    max_retries: int = 3                         # 最大重试次数

    # 报告
    report: str | None = None                    # Markdown 报告正文
    report_ready: bool = False
    citations_valid: bool = False

    # 控制字段
    current_step: str = "init"                   # 当前步骤名称，用于前端展示
    errors: list[str] = field(default_factory=list)  # 所有错误日志
    completed: bool = False                      # 是否完成
```

### execution.py

```python
from dataclasses import dataclass

@dataclass
class ExecutionArtifact:
    success: bool                                # 是否成功
    stdout: str                                  # 标准输出
    stderr: str                                  # 标准错误
    traceback: str | None                        # 异常回溯
    generated_files: list[str]                   # 生成的图表文件路径列表
    data_files: list[str]                        # 生成的数据文件路径列表
    execution_time_ms: int                       # 执行耗时
    exit_code: int                               # 退出码
```

### reporting.py

```python
from dataclasses import dataclass

@dataclass
class Citation:
    citation_id: str                             # cite_{uuid}
    claim: str                                   # 结论片段
    source_doc_id: str                           # 来源文档 ID
    source_filename: str                         # 来源文件名
    page_num: int | None                         # 页码
    chunk_id: str                                # 对应 chunk
    source_type: str                             # "local_literature" | "web_search" | "data_analysis"
    confidence: float                            # 置信度 0-1

@dataclass
class ReportBundle:
    task_id: str
    query: str
    report_markdown: str                         # Markdown 报告正文
    citations: list[dict]                        # Citation 的 dict 形态
    chart_paths: list[str]                       # 图表路径
    log_paths: list[str]                         # 日志路径
    generated_at: str                            # 生成时间 ISO
```

## 所有数据结构必须支持的契约

1. **JSON 序列化**：所有 dataclass 都要有 `to_dict()` 方法（或直接 `dataclasses.asdict()`）
2. **类型注解完整**：所有字段要有 Python 类型注解，不能是 `Any`
3. **可空字段显式标注**：`str | None` / `int | None`，不要省略
4. **默认值合理**：list 默认 `field(default_factory=list)`，不要用可变默认值
5. **不要引入外部依赖**：只使用 `dataclasses` 和 `enum`，不要引入 pydantic、numpy 等

## 与上下游模块的对接

- **上游**：无。这是最底层。
- **下游**：所有模块 import `adaptive_crag.schema` 中的数据结构
- **对接方式**：模块间通过 import dataclass 传递数据，不传裸 dict

## 测试要点

- 每个数据类都能用字段构造
- `dataclasses.asdict()` 能正确序列化
- Enum 字段能正确序列化/反序列化
- 可空字段能正确处理 None
- 嵌套数据类能正确构造