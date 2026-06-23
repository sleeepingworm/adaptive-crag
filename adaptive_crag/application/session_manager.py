"""
会话管理：管理 Streamlit 会话中的任务状态。
线程安全版本：后台线程写入内存 dict，Streamlit 主线程同步到 session_state。
"""

import uuid
import threading
from dataclasses import dataclass, field
from datetime import datetime
from copy import deepcopy


@dataclass
class TaskRun:
    """单个任务的运行时状态"""
    task_id: str
    query: str
    uploaded_files: list[str] = field(default_factory=list)
    status: str = "pending"  # pending | running | completed | failed | cancelled
    created_at: str = ""
    completed_at: str | None = None
    graph_state: dict | None = None
    events: list[dict] = field(default_factory=list)
    report: str | None = None
    artifact_dir: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "query": self.query,
            "uploaded_files": self.uploaded_files,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "events": self.events,
            "report": self.report,
            "artifact_dir": self.artifact_dir,
            "error": self.error,
            "current_step": (self.graph_state or {}).get("current_step", "init") if self.graph_state else "init",
        }


@dataclass
class Session:
    """一个 Streamlit 会话"""
    session_id: str
    tasks: dict[str, TaskRun] = field(default_factory=dict)
    current_task_id: str | None = None

    @property
    def current_task(self) -> TaskRun | None:
        if self.current_task_id and self.current_task_id in self.tasks:
            return self.tasks[self.current_task_id]
        return None


# ============================================================
# 线程安全的内存存储（后台线程和主线程共用）
# ============================================================
_lock = threading.Lock()
_memory_session: Session | None = None


def _get_memory_session() -> Session:
    """获取或创建线程安全的内存 Session（无 st.session_state 依赖）"""
    global _memory_session
    if _memory_session is None:
        _memory_session = Session(session_id=str(uuid.uuid4()))
    return _memory_session


class SessionManager:
    """
    管理 Streamlit 会话中的任务状态。

    工作机制：
    - 后台线程（如 TaskOrchestrator）通过 _lock 直接读写 _memory_session
    - Streamlit 主线程在 get_session() 时从 _memory_session 同步到 st.session_state
    """

    SESSION_KEY = "_crag_session"

    @staticmethod
    def get_session() -> Session:
        """
        从 st.session_state 获取或创建 Session，
        并将内存中的最新状态同步进去。
        线程安全：仅限 Streamlit 主线程调用。
        """
        import streamlit as st

        mem = _get_memory_session()

        # 同步内存状态到 st.session_state
        if SessionManager.SESSION_KEY not in st.session_state:
            st.session_state[SessionManager.SESSION_KEY] = deepcopy(mem)
        else:
            stored = st.session_state[SessionManager.SESSION_KEY]
            # 只同步 task 数据（session_id 由 st 管理）
            with _lock:
                for tid, task in mem.tasks.items():
                    stored.tasks[tid] = task
                if mem.current_task_id:
                    stored.current_task_id = mem.current_task_id

        return st.session_state[SessionManager.SESSION_KEY]

    @staticmethod
    def create_task(query: str, files: list[str] | None = None) -> str:
        """创建新任务，返回 task_id"""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        task = TaskRun(
            task_id=task_id,
            query=query,
            uploaded_files=files or [],
            status="pending",
            created_at=datetime.now().isoformat(),
        )
        with _lock:
            session = _get_memory_session()
            session.tasks[task_id] = task
            session.current_task_id = task_id
        return task_id

    @staticmethod
    def get_task(task_id: str) -> TaskRun | None:
        """获取指定任务"""
        with _lock:
            session = _get_memory_session()
            task = session.tasks.get(task_id)
            if task is not None:
                task = deepcopy(task)
        return task

    @staticmethod
    def update_task(task_id: str, **kwargs):
        """更新任务字段（线程安全）"""
        with _lock:
            mem = _get_memory_session()
            task = mem.tasks.get(task_id)
            if task is None:
                return
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

    @staticmethod
    def list_tasks() -> list[TaskRun]:
        """列出当前会话所有任务"""
        with _lock:
            session = _get_memory_session()
            tasks = [deepcopy(t) for t in session.tasks.values()]
        return tasks

    @staticmethod
    def add_event(task_id: str, event: dict):
        """为任务添加事件（线程安全）"""
        with _lock:
            mem = _get_memory_session()
            task = mem.tasks.get(task_id)
            if task:
                task.events.append(event)

    @staticmethod
    def get_current_task_id() -> str | None:
        """获取当前任务 ID"""
        with _lock:
            session = _get_memory_session()
            return session.current_task_id

    @staticmethod
    def set_current_task(task_id: str):
        """设置当前任务"""
        with _lock:
            session = _get_memory_session()
            session.current_task_id = task_id