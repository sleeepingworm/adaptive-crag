"""
adaptive_crag.schema - 共享数据结构定义
=======================================
所有模块共用的数据类定义，使用 Python dataclass。
不包含任何业务逻辑，不引入外部依赖。
"""

from .documents import Document, Chunk, DatasetProfile, DocumentType, ChunkStrategy
from .retrieval import SearchResult, EvidenceSet
from .workflow import GraphState, TaskPlan, TaskType, CodePlan
from .execution import ExecutionArtifact
from .reporting import Citation, ReportBundle
from .evaluation import BenchmarkCase, BenchmarkResult

__all__ = [
    # documents
    "Document", "Chunk", "DatasetProfile", "DocumentType", "ChunkStrategy",
    # retrieval
    "SearchResult", "EvidenceSet",
    # workflow
    "GraphState", "TaskPlan", "TaskType", "CodePlan",
    # execution
    "ExecutionArtifact",
    # reporting
    "Citation", "ReportBundle",
    # evaluation
    "BenchmarkCase", "BenchmarkResult",
]
