# 单元测试说明书：LangGraph 工作流 (graph)

## 对应模块
`08_graph.md`

## 目标测试文件
```
tests/
    test_graph/
        __init__.py
        conftest.py              # 构建好的 LangGraph 实例 fixture
        test_workflow_structure.py  # 工作流结构
        test_conditions.py       # 条件边逻辑
        test_paths.py            # 不同路径的集成测试
```

## 运行方式
```bash
pytest tests/test_graph/ -v
```

## 测试策略
- 使用真实构建的 LangGraph 实例
- 每个节点函数用 mock 模拟（不调用真实 LLM 和检索）
- 测试重点是：条件边判断逻辑正确、路径符合预期、状态传递无误

## conftest.py 关键 fixture

```python
@pytest.fixture
def mock_graph_nodes(monkeypatch):
    """用简单的 return dict 替换所有节点函数"""

@pytest.fixture
def built_graph(mock_graph_nodes):
    """build_workflow() 返回的 Graph 对象"""

@pytest.fixture
def initial_state():
    """基础 GraphState，只设置 query 和 uploaded_files"""

@pytest.fixture
def state_with_evidence():
    """证据足够的 GraphState"""

@pytest.fixture
def state_without_evidence():
    """证据不足的 GraphState"""

@pytest.fixture
def state_code_success():
    """代码执行成功的 GraphState"""

@pytest.fixture
def state_code_failed():
    """代码执行失败的 GraphState"""

@pytest.fixture
def state_code_retry_exhausted():
    """重试次数已超限的 GraphState"""
```

## 测试用例清单

### test_workflow_structure.py

```python
def test_workflow_builds():
    """build_workflow() 返回 StateGraph 实例"""

def test_workflow_has_10_nodes(built_graph):
    """工作流包含 10 个节点"""

def test_workflow_has_all_required_nodes(built_graph):
    """节点列表包含: route/retrieve/grade/web_search/analyze/code_write/execute/repair/report/validate"""

def test_workflow_entry_point(built_graph):
    """入口节点是 route"""

def test_workflow_ends_at_end(built_graph):
    """validate 节点的下一个节点是 END"""

def test_workflow_conditional_edges(built_graph):
    """存在条件边: grade/analyze/execute"""

def test_workflow_can_print(built_graph):
    """workflow.get_graph().print_ascii() 不报错"""
```

### test_conditions.py

```python
def test_after_grade_sufficient(state_with_evidence):
    """evidence_ready=True -> "sufficient""""

def test_after_grade_insufficient(state_without_evidence):
    """evidence_ready=False -> "insufficient""""

def test_after_analyze_needs_code(state_with_code_required):
    """requires_code=True -> "need_code""""

def test_after_analyze_no_code(state_without_code):
    """requires_code=False -> "no_code""""

def test_after_execute_success(state_code_success):
    """execution_result.success=True -> "success""""

def test_after_execute_retry(state_code_failed):
    """执行失败且 retry_count < max_retries -> "retry""""

def test_after_execute_give_up(state_code_retry_exhausted):
    """执行失败且 retry_count >= max_retries -> "give_up""""
```

### test_paths.py

```python
def test_path_grade_to_analyze(built_graph, state_with_evidence):
    """证据足够时路径: route -> retrieve -> grade -> analyze"""

def test_path_grade_to_web(built_graph, state_without_evidence):
    """证据不足时路径: route -> retrieve -> grade -> web_search -> grade"""

def test_path_analyze_to_report(built_graph, state_no_code):
    """不需要代码时路径: ... -> analyze -> report"""

def test_path_analyze_to_code(built_graph, state_code_required):
    """需要代码时路径: ... -> analyze -> code_write -> execute"""

def test_path_execute_to_repair(built_graph, state_execution_failed):
    """执行失败时路径: ... -> execute -> repair -> execute"""

def test_path_execute_to_report_on_success(built_graph, state_execution_success):
    """执行成功时路径: ... -> execute -> report"""

def test_path_execute_to_report_on_give_up(built_graph, state_retry_exhausted):
    """重试超限时路径: ... -> execute -> report（跳过 repair）"""

def test_complete_path_with_code(built_graph, state_code_success):
    """完整路径：route -> retrieve -> grade -> analyze -> code_write -> execute -> report -> validate -> END"""

def test_complete_path_without_code(built_graph, state_no_code):
    """完整路径：route -> retrieve -> grade -> analyze -> report -> validate -> END"""

def test_state_persists_across_nodes(built_graph, initial_state):
    """节点间状态传递正确，不丢失字段"""
```