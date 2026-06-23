# 单元测试说明书：共享数据结构 (schema)

## 对应模块
`01_schema.md`

## 目标测试文件
```
tests/
    __init__.py
    conftest.py                # 共享 fixture
    test_schema/
        __init__.py
        test_documents.py      # Document, Chunk, DatasetProfile
        test_workflow.py       # GraphState, TaskPlan
        test_execution.py      # ExecutionArtifact
        test_reporting.py      # Citation, ReportBundle
        test_evaluation.py     # BenchmarkCase, BenchmarkResult
```

## 运行方式
```bash
cd {project_root}
pytest tests/test_schema/ -v
```

## 通用测试要求

- 每个数据类都要测：正常构造、字段默认值、可空字段、JSON 序列化
- Enum 字段测：值枚举完整、字符串转换
- 不需要外部依赖（不需要 ChromaDB、不需要 LLM）
- 所有测试纯内存，不读写磁盘
- 测试数据固定写死，不随机生成

## 测试用例清单

### test_documents.py

```python
# 文件: tests/test_schema/test_documents.py

def test_document_creation():
    """Document 能用所有必填字段正确构造"""

def test_document_optional_fields():
    """Document 的可空字段默认为 None"""

def test_document_serialization():
    """dataclasses.asdict(document) 正确序列化所有字段"""

def test_chunk_creation():
    """Chunk 能用必填字段正确构造"""

def test_chunk_default_strategy():
    """Chunk 的 strategy 默认值为 PARAGRAPH"""

def test_chunk_optional_embedding():
    """Chunk 的 embedding 默认是 None，设值后不为 None"""

def test_chunk_serialization():
    """Chunk 序列化后 embedding 字段正确处理 None"""

def test_dataset_profile_creation():
    """DatasetProfile 能用字段正确构造"""

def test_dataset_profile_columns():
    """columns 列表中的每个 dict 包含 name/dtype/missing/sample"""

def test_document_type_enum_values():
    """DocumentType 枚举包含 PDF/TXT/MARKDOWN/CSV/EXCEL"""

def test_chunk_strategy_enum_values():
    """ChunkStrategy 枚举包含 PARAGRAPH/FIXED_TOKEN/HEADING"""
```

### test_workflow.py

```python
# 文件: tests/test_schema/test_workflow.py

def test_task_plan_creation():
    """TaskPlan 能用必填字段正确构造"""

def test_task_plan_defaults():
    """TaskPlan 的 requires_code/requires_web_search 默认 False"""

def test_task_plan_serialization():
    """TaskPlan 序列化后 sub_tasks 列表保留结构"""

def test_graph_state_creation():
    """GraphState 能用 query 和 uploaded_files 构造"""

def test_graph_state_default_fields():
    """
    GraphState 的默认值:
    - plan = None
    - retrieved_chunks = [] (空列表，不是 None)
    - retry_count = 0
    - max_retries = 3
    - current_step = "init"
    - completed = False
    """

def test_graph_state_increment_retry():
    """retry_count 能正常加 1"""

def test_graph_state_serialization():
    """GraphState 序列化全部字段，包括嵌套的 plan"""

def test_task_type_enum_values():
    """TaskType 枚举包含 LITERATURE_SEARCH/DATA_ANALYSIS/HYBRID"""
```

### test_execution.py

```python
# 文件: tests/test_schema/test_execution.py

def test_execution_artifact_success():
    """构造一个成功的 ExecutionArtifact"""

def test_execution_artifact_failure():
    """构造一个失败的 ExecutionArtifact（有 traceback）"""

def test_execution_artifact_defaults():
    """generated_files 和 data_files 默认为 []"""

def test_execution_artifact_serialization():
    """序列化后所有字段保留"""

def test_execution_artifact_empty_stdout():
    """stdout 为空字符串时可正常构造"""
```

### test_reporting.py

```python
# 文件: tests/test_schema/test_reporting.py

def test_citation_creation():
    """Citation 用必填字段正确构造"""

def test_citation_optional_page_num():
    """page_num 可为 None"""

def test_citation_confidence_range():
    """confidence 在 0-1 范围内（由调用方保证，不强校验类型）"""

def test_citation_serialization():
    """序列化后保留所有字段"""

def test_report_bundle_creation():
    """ReportBundle 用必填字段正确构造"""

def test_report_bundle_optional_lists():
    """chart_paths/log_paths 默认为空列表"""

def test_report_bundle_serialization():
    """序列化后 citations 列表保留"""

def test_citation_source_type_values():
    """
    source_type 取值:
    - "local_literature"
    - "web_search"
    - "data_analysis"
    """
```

### test_evaluation.py

```python
# 文件: tests/test_schema/test_evaluation.py

def test_benchmark_case_creation():
    """BenchmarkCase 用必填字段正确构造"""

def test_benchmark_result_creation():
    """BenchmarkResult 用字段正确构造"""

def test_benchmark_case_scoring_rules():
    """scoring_rules dict 至少包含 requires_citation"""

def test_benchmark_result_defaults():
    """无对应字段时默认 None 或 0"""
```