"""
会话管理：管理 Streamlit 会话中的任务状态。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


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


class SessionManager:
    """
    管理 Streamlit 会话中的任务状态。
    通过 st.session_state 存取，兼容 Streamlit rerun 机制。
    """

    SESSION_KEY = "_crag_session"

    @staticmethod
    def get_session() -> Session:
        """从 streamlit.session_state 获取或创建 Session"""
        import streamlit as st

        if SessionManager.SESSION_KEY not in st.session_state:
            st.session_state[SessionManager.SESSION_KEY] = Session(
                session_id=str(uuid.uuid4()),
            )
        return st.session_state[SessionManager.SESSION_KEY]

    @staticmethod
    def create_task(query: str, files: list[str] | None = None) -> str:
        """创建新任务，返回 task_id"""
        session = SessionManager.get_session()
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        task = TaskRun(
            task_id=task_id,
            query=query,
            uploaded_files=files or [],
            status="pending",
            created_at=datetime.now().isoformat(),
        )
        session.tasks[task_id] = task
        session.current_task_id = task_id
        return task_id

    @staticmethod
    def get_task(task_id: str) -> TaskRun | None:
        """获取指定任务"""
        session = SessionManager.get_session()
        return session.tasks.get(task_id)

    @staticmethod
    def update_task(task_id: str, **kwargs):
        """更新任务字段"""
        session = SessionManager.get_session()
        task = session.tasks.get(task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)

    @staticmethod
    def list_tasks() -> list[TaskRun]:
        """列出当前会话所有任务"""
        session = SessionManager.get_session()
        return list(session.tasks.values())

    @staticmethod
    def add_event(task_id: str, event: dict):
        """为任务添加事件"""
        session = SessionManager.get_session()
        task = session.tasks.get(task_id)
        if task:
            task.events.append(event)

    @staticmethod
    def get_current_task_id() -> str | None:
        """获取当前任务 ID"""
        session = SessionManager.get_session()
        return session.current_task_id

    @staticmethod
    def set_current_task(task_id: str):
        """设置当前任务"""
        session = SessionManager.get_session()
        session.current_task_id = task_id
