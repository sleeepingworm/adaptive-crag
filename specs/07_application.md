# 模块说明书：应用编排层 (application)

## 所属层级
应用编排层

## 目标目录
`adaptive_crag/application/`

生成文件：
```
adaptive_crag/application/
    __init__.py             # 导出 TaskOrchestrator
    session_manager.py      # 会话管理
    task_orchestrator.py    # 任务编排
    artifact_manager.py     # 产物管理
```

## 依赖模块

- **必须先生成**：`01_schema`（使用 GraphState, TaskPlan, ReportBundle）
- **必须先生成**：`02_config`（使用 AppConfig）
- **必须先生成**：`03_ingestion`（调用 IngestionPipeline）
- **必须先生成**：`07_graph`（启动 LangGraph 工作流）

## 职责边界

**做：**
- 管理一次 Streamlit 会话内的多任务切换
- 管理用户任务的生命周期（创建、执行、完成、取消）
- 在任务启动时：组织文件、创建产物目录、初始化 GraphState
- 在任务运行时：接收 LangGraph 事件链、转为前端可展示的阶段
- 在任务完成后：组织产物索引、记录日志

**不做：**
- 不做 Streamlit 页面渲染
- 不做 LLM 调用
- 不做文件内容解析
- 不做检索和检索判断

## 核心接口

### session_manager.py

```python
import uuid
from dataclasses import dataclass, field

@dataclass
class Session:
    session_id: str                    # Streamlit session_id 或生成的 uuid
    tasks: dict[str, "TaskRun"] = field(default_factory=dict)  # task_id -> TaskRun
    current_task_id: str | None = None

@dataclass
class TaskRun:
    task_id: str                       # uuid
    query: str                         # 用户问题
    uploaded_files: list[str]          # 上传文件路径
    status: str                        # "pending" | "running" | "completed" | "failed" | "cancelled"
    created_at: str                    # ISO 时间
    completed_at: str | None = None
    graph_state: dict | None = None    # GraphState 的 dict 形态
    events: list[dict] = field(default_factory=list)  # 执行事件链
    report: str | None = None
    artifact_dir: str | None = None
    error: str | None = None

class SessionManager:
    """
    管理 Streamlit 会话中的任务状态。
    Streamlit 每次 rerun 会清空 Python 变量，
    所以状态需存在 st.session_state 中。
    """

    @staticmethod
    def get_session() -> Session:
        """从 streamlit.session_state 获取或创建 Session"""

    @staticmethod
    def create_task(query: str, files: list[str]) -> str:
        """创建新任务，返回 task_id"""

    @staticmethod
    def get_task(task_id: str) -> TaskRun | None:
        """获取指定任务"""

    @staticmethod
    def update_task(task_id: str, **kwargs):
        """更新任务字段"""

    @staticmethod
    def list_tasks() -> list[TaskRun]:
        """列出当前会话所有任务"""
```

### task_orchestrator.py

```python
class TaskOrchestrator:
    """
    任务编排器。协调文件解析、工作流执行、产物管理的完整流程。
    """

    def __init__(self, config: AppConfig):
        self.config = config
        self.ingestion = IngestionPipeline(max_tokens=config.retrieval.chunk_max_tokens)
        # workflow 在 start_task 时创建（因为初始化需要索引）

    def start_task(self, session: Session, task_id: str) -> None:
        """
    启动一个任务。

    流程:
    1. 获取 TaskRun
    2. 为任务创建专属产物目录 data/artifacts/{task_id}/
    3. 对每个上传文件运行 IngestionPipeline.process()
    4. 收集所有 Document + Chunk
    5. 将 Chunk 写入检索索引（调用 retrieval 模块）
    6. 构造初始 GraphState
    7. 启动 LangGraph 工作流
    8. 将事件写入 TaskRun.events
    """

    def cancel_task(self, task_id: str) -> None:
        """取消正在执行的任务。标记状态即可，不强制终止进程。"""

    def get_task_events(self, task_id: str) -> list[dict]:
        """获取任务的事件列表，供前端展示进度。"""

    def get_task_status(self, task_id: str) -> dict:
        """
        返回当前状态的摘要，供页面层轮询：
        {
            "status": "running",
            "current_step": "retrieving",
            "progress": 0.45,
            "elapsed_seconds": 12.3
        }
        """
```

### artifact_manager.py

```python
class ArtifactManager:
    """
    管理一次任务的产物目录结构和产物索引。
    """

    def __init__(self, root_artifact_dir: str, task_id: str):
        """
        产物目录结构:
        data/artifacts/{task_id}/
            charts/          # 图表文件
            data/            # 生成的数据文件
            logs/            # 执行日志
            report.md        # 最终报告
            report.pdf       # PDF 报告
            citations.json   # 引用映射
            evidence.json    # 证据包
        """

    def ensure_dirs(self) -> str:
        """创建产物目录，返回根目录路径"""

    def save_report(self, report_md: str) -> str:
        """保存 Markdown 报告，返回路径"""

    def save_citations(self, citations: list[dict]) -> str:
        """保存引用映射为 JSON"""

    def save_event_log(self, event: dict) -> None:
        """追加记录一条事件日志"""

    def collect_charts(self) -> list[str]:
        """扫描 charts/ 目录，返回所有图片路径"""

    def build_report_bundle(self, report_md: str, citations: list[dict]) -> ReportBundle:
        """构造 ReportBundle 对象"""
```

## 实现约束

1. **Streamlit 兼容**：SessionManager 必须通过 `st.session_state` 存取，不能依赖 Python 全局变量
2. **异步简化**：MVP 阶段 LangGraph 以同步方式运行，不要用 asyncio
3. **任务隔离**：每个任务的产物目录相互独立，不影响
4. **状态持久化**：至少将 TaskRun 基本信息持久化（可用 JSON 文件），防止 Streamlit rerun 导致状态丢失
5. **事件链**：事件格式统一为 `{"step": str, "status": str, "message": str, "timestamp": str}`

## 与上下游模块的对接

- **上游调用方**：Streamlit 页面层
- **下游调用方**：ingestion 模块（解析文件）、retrieval 模块（建立索引）、graph 模块（执行工作流）
- **数据流向**：`用户操作 -> SessionManager.create_task() -> TaskOrchestrator.start_task() -> ingestion -> retrieval -> graph`

## 测试要点

- 创建任务后能在产物目录中找到对应文件夹
- 多任务隔离：task1 的产物不影响 task2
- 文件解析失败时任务能正确标记为 failed
- 事件链能正确记录工作流进度