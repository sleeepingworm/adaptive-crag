"""
adaptive_crag.application - 应用编排层
=====================================
管理会话、任务生命周期、产物目录。
"""

from .session_manager import SessionManager, Session, TaskRun
from .task_orchestrator import TaskOrchestrator
from .artifact_manager import ArtifactManager

__all__ = [
    "SessionManager",
    "Session",
    "TaskRun",
    "TaskOrchestrator",
    "ArtifactManager",
]
