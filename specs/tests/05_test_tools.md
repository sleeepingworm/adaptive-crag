# 单元测试说明书：工具能力层 (tools)

## 对应模块
`05_tools.md`

## 目标测试文件
```
tests/
    test_tools/
        __init__.py
        conftest.py              # mock 底层模块的 fixture
        test_hybrid_search.py    # 混合检索工具
        test_vector_search.py    # 向量检索工具
        test_bm25_search.py      # BM25 检索工具
        test_web_search.py       # 联网搜索工具
        test_sandbox_executor.py # 沙箱执行工具
        test_citation_lookup.py  # 引用反查工具
        test_artifact_reader.py  # 产物读取工具
```

## 运行方式
```bash
pytest tests/test_tools/ -v
```

## 测试策略
- **不调用真实底层模块**：使用 unittest.mock 模拟 retrieval/sandbox/reporting
- 只测工具函数的：参数校验、返回值格式、错误处理
- 一个 mock 对应一个底层能力

## conftest.py mock 策略

```python
@pytest.fixture(autouse=True)
def mock_retrieval(monkeypatch):
    """mock adaptive_crag.retrieval.hybrid_retriever 的 search"""

@pytest.fixture(autouse=True)
def mock_web_search(monkeypatch):
    """mock adaptive_crag.tools.web_search 的网络请求"""

@pytest.fixture(autouse=True)
def mock_sandbox(monkeypatch):
    """mock adaptive_crag.sandbox.runner.SandboxRunner.execute"""

@pytest.fixture(autouse=True)
def mock_citation(monkeypatch):
    """mock adaptive_crag.ingestion.citation_mapper"""
```

## 测试用例清单

### test_hybrid_search.py

```python
def test_hybrid_search_success(mock_retrieval):
    """正常返回包含 success=True 和 result"""

def test_hybrid_search_result_structure():
    """result 包含 query/results/total_found"""

def test_hybrid_search_missing_query():
    """不传 query 返回 success=False"""

def test_hybrid_search_empty_index(mock_empty_retrieval):
    """索引为空时返回 success=False, error 包含 "索引为空""""

def test_hybrid_search_top_k_default():
    """不传 top_k 使用默认 10"""

def test_hybrid_search_top_k_custom():
    """传 top_k=5 返回 5 条结果"""
```

### test_vector_search.py / test_bm25_search.py

```python
def test_vector_search_success():
    """向量检索成功返回"""
def test_vector_search_missing_query():
    """缺参数返回错误"""
def test_bm25_search_exact_match():
    """关键词精确匹配返回结果"""
def test_bm25_search_no_match():
    """关键词无匹配返回空列表"""
```

### test_web_search.py

```python
def test_web_search_success(mock_web_search):
    """成功的联网搜索返回 title/url/snippet/content"""

def test_web_search_no_api_key(mock_no_api_key):
    """未配置 API Key 时返回 success=False"""

def test_web_search_empty_query():
    """空 query 返回 success=False"""

def test_web_search_result_limit(mock_web_search):
    """max_results=3 返回 3 条"""

def test_web_search_network_error(mock_network_error):
    """网络异常时返回 success=False, error 包含异常信息"""
```

### test_sandbox_executor.py

```python
def test_sandbox_executor_success(mock_sandbox_success):
    """成功执行返回 stdout/exit_code=0/generated_files"""

def test_sandbox_executor_failure(mock_sandbox_failure):
    """执行失败返回 stderr/traceback/exit_code=1"""

def test_sandbox_executor_missing_code():
    """不传 code 返回 success=False"""

def test_sandbox_executor_missing_output_dir():
    """不传 output_dir 返回 success=False"""

def test_sandbox_executor_timeout(mock_sandbox_timeout):
    """超时返回 success=False, error 包含 "超时""""
```

### test_citation_lookup.py

```python
def test_citation_lookup_found(mock_citation):
    """chunk_id 存在时返回 doc_id/filename/page_num/text_snippet"""

def test_citation_lookup_not_found(mock_citation_empty):
    """chunk_id 不存在时返回 success=False"""

def test_citation_lookup_missing_chunk_id():
    """不传 chunk_id 返回错误"""
```

### test_artifact_reader.py

```python
def test_artifact_reader_chart(mock_chart_file):
    """读取图表返回 type/content/path"""

def test_artifact_reader_log(mock_log_file):
    """读取日志返回文本内容"""

def test_artifact_reader_not_found(mock_nonexistent):
    """文件不存在返回 success=False"""

def test_artifact_reader_missing_params():
    """缺参数返回错误"""
```

### 工具注册表测试

```python
def test_tool_registry_has_all_tools():
    """TOOL_REGISTRY 包含所有 7 个工具"""

def test_each_tool_has_name_description_parameters():
    """每个工具注册项包含 name/description/parameters"""

def test_each_tool_has_required_fields():
    """每个工具的 parameters 中 required 字段存在"""
```