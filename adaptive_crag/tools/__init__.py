"""
adaptive_crag.tools - 工具能力层
===============================
把底层能力封装成 Agent 可调用的工具函数。
统一输入/输出为 dict 格式，包含成功/失败状态。
"""

from .hybrid_search import hybrid_search
from .vector_search import vector_search
from .bm25_search import bm25_search
from .web_search import web_search
from .sandbox_executor import sandbox_executor
from .citation_lookup import citation_lookup
from .artifact_reader import artifact_reader

# 工具注册表（用于 Agent 系统提示词）
TOOL_REGISTRY = {
    "hybrid_search": {
        "name": "hybrid_search",
        "description": "从本地知识库同时使用向量检索和关键词检索召回相关文献片段。适合需要快速找到相关文献段落的问题。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词或问题"},
                "top_k": {"type": "integer", "description": "返回结果数量", "default": 10},
            },
            "required": ["query"],
        },
    },
    "vector_search": {
        "name": "vector_search",
        "description": "纯向量语义检索，适合查找与问题语义相似的文献段落。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词或问题"},
                "top_k": {"type": "integer", "description": "返回结果数量", "default": 10},
            },
            "required": ["query"],
        },
    },
    "bm25_search": {
        "name": "bm25_search",
        "description": "关键词精确检索，适合查找函数名、公式、缩写等精确匹配场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "top_k": {"type": "integer", "description": "返回结果数量", "default": 10},
            },
            "required": ["query"],
        },
    },
    "web_search": {
        "name": "web_search",
        "description": "当本地知识库找不到足够信息时，从互联网搜索最新信息。适合当前事件、新技术、本地材料缺失的场景。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "max_results": {"type": "integer", "description": "返回结果数量", "default": 5},
            },
            "required": ["query"],
        },
    },
    "sandbox_executor": {
        "name": "sandbox_executor",
        "description": "在隔离沙箱中执行 Python 数据分析代码。支持 pandas、numpy、matplotlib、seaborn 等库。代码运行有 60 秒超时限制。",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的 Python 代码"},
                "data_files": {
                    "type": "array", "items": {"type": "string"},
                    "description": "数据文件路径列表",
                },
                "output_dir": {"type": "string", "description": "输出目录"},
            },
            "required": ["code", "output_dir"],
        },
    },
    "citation_lookup": {
        "name": "citation_lookup",
        "description": "根据 chunk_id 反查原文内容和来源信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "chunk_id": {"type": "string", "description": "Chunk ID"},
                "doc_id": {"type": "string", "description": "文档 ID（可选）"},
            },
            "required": ["chunk_id"],
        },
    },
    "artifact_reader": {
        "name": "artifact_reader",
        "description": "读取任务产物的内容（图表、日志、报告、数据文件）。",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务 ID"},
                "artifact_type": {
                    "type": "string",
                    "enum": ["chart", "log", "report", "data"],
                    "description": "产物类型",
                },
                "path": {"type": "string", "description": "产物路径"},
            },
            "required": ["task_id", "artifact_type", "path"],
        },
    },
}

__all__ = [
    "hybrid_search",
    "vector_search",
    "bm25_search",
    "web_search",
    "sandbox_executor",
    "citation_lookup",
    "artifact_reader",
    "TOOL_REGISTRY",
]
