# 单元测试说明书：应用编排层 (application)

## 对应模块
`07_application.md`

## 目标测试文件
```
tests/
    test_application/
        __init__.py
        conftest.py              # 模拟 Session 和 Graph 的 fixture
        test_session_manager.py  # Session 管理
        test_task_orchestrator.py # 任务编排
        test_artifact_manager.py # 产物管理
```

## 运行方式
```bash
pytest tests/test_application/ -v
```

## 测试策略
- SessionManager 需要模拟 `st.session_state`（不引入 Streamlit，用 dict 模拟）
- TaskOrchestrator 用 mock 模拟 ingestion 和 graph 的调用
- ArtifactManager 真的在临时目录读写文件

## conftest.py 关键 fixture

```python
@pytest.fixture
def mock_streamlit_session(monkeypatch):
    """用 dict 模拟 st.session_state，避免引入 Streamlit"""

@pytest.fixture
def mock_ingestion_pipeline(monkeypatch):
    """模拟 IngestionPipeline.process 返回固定 Document + Chunk"""

@pytest.fixture
def mock_graph_workflow(monkeypatch):
    """模拟 LangGraph 的 invoke 返回固定 GraphState"""

@pytest.fixture
def temp_artifact_dir(tmp_path):
    """临时产物目录"""
```

## 测试用例清单

### test_session_manager.py

```python
def test_get_session_creates_new(mock_streamlit_session):
    """首次调用 get_session 创建新 Session"""

def test_get_session_reuses_existing(mock_streamlit_session):
    """第二次调用 get_session 返回同一个 Session 实例"""

def test_create_task_returns_id(mock_streamlit_session):
    """create_task 返回非空字符串 task_id"""

def test_create_task_stores_task(mock_streamlit_session):
    """create_task 后 get_task 能找到该任务"""

def test_create_task_initial_status(mock_streamlit_session):
    """新创建的任务 status == "pending""""

def test_update_task_fields(mock_streamlit_session):
    """update_task 能修改 status 和 report 字段"""

def test_get_task_not_found(mock_streamlit_session):
    """不存在的 task_id 返回 None"""

def test_list_tasks_empty(mock_streamlit_session):
    """没有任何任务时 list_tasks() 返回 []"""

def test_list_tasks_returns_all(mock_streamlit_session):
    """添加 3 个任务后返回 3 条"""

def test_current_task_id(mock_streamlit_session):
    """创建任务后 current_task_id 被更新"""
```

### test_task_orchestrator.py

```python
def test_start_task_changes_status(orchestrator, mock_session, mock_ingestion_pipeline, mock_graph_workflow):
    """start_task 后任务 status 变成 "running""""

def test_start_task_creates_artifact_dir(orchestrator, mock_session, mock_ingestion_pipeline, mock_graph_workflow, temp_artifact_dir):
    """任务开始后产物目录被创建"""

def test_start_task_calls_ingestion(orchestrator, mock_session, mock_ingestion_pipeline, mock_graph_workflow):
    """任务开始后每个上传文件都调用了 ingestion"""

def test_start_task_calls_graph(orchestrator, mock_session, mock_ingestion_pipeline, mock_graph_workflow):
    """文件解析后调用了 graph.invoke"""

def test_task_completed_has_events(orchestrator, mock_session, mock_ingestion_pipeline, mock_graph_workflow):
    """任务完成后 events 不为空"""

def test_start_task_no_files(orchestrator, mock_session, mock_ingestion_pipeline, mock_graph_workflow):
    """没有上传文件的任务也能正常开始（纯联网搜索）"""

def test_cancel_task(orchestrator, mock_session):
    """取消后状态变为 "cancelled""""

def test_get_task_status_running(mock_session):
    """运行中的任务返回 status/current_step/progress/elapsed_seconds"""

def test_get_task_events_empty(mock_session):
    """无事件时返回 []"""
```

### test_artifact_manager.py

```python
def test_ensure_dirs_creates(artifact_manager, temp_artifact_dir):
    """ensure_dirs 创建 charts/data/logs 子目录"""

def test_save_report_creates_file(artifact_manager, temp_artifact_dir):
    """save_report 创建 report.md 文件"""

def test_save_citations_creates_json(artifact_manager, temp_artifact_dir):
    """save_citations 创建 citations.json"""

def test_save_event_log_append(artifact_manager, temp_artifact_dir):
    """save_event_log 追加内容到事件日志"""

def test_collect_charts_empty(artifact_manager, temp_artifact_dir):
    """无图表时返回 []"""

def test_collect_charts_with_files(artifact_manager, temp_artifact_dir, sample_chart):
    """有图表时返回正确路径列表"""

def test_build_report_bundle_structure(artifact_manager, temp_artifact_dir):
    """build_report_bundle 返回 ReportBundle 格式的 dict"""
```