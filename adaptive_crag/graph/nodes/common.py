"""
graph 节点公共工具。
提供 @node_handler 装饰器统一处理 check_abort、事件日志、状态透传、异常兜底。
"""

import threading
from datetime import datetime
from functools import wraps

# 线程本地存储 —— 绕开 LangGraph 状态限制，传递无法序列化的对象
_registry = threading.local()


def set_current_retriever(retriever):
    """设置当前线程的检索器（由 Orchestrator 在任务启动前调用）"""
    _registry.retriever = retriever


def set_current_mappings(mappings: dict):
    """设置当前线程的引用映射（由 Orchestrator 在任务启动前调用）"""
    _registry.mappings = mappings


def get_current_retriever():
    return getattr(_registry, 'retriever', None)


def get_current_mappings() -> dict:
    return getattr(_registry, 'mappings', {})


def node_handler(step_name: str, running_message: str):
    """
    节点装饰器。
    自动处理：check_abort 检查 → 日志 → emit_event → query/uploaded_files 透传 → 统一异常兜底。

    用法：
        @node_handler("retrieve", "正在检索文献...")
        def retrieve_node(state: dict) -> dict:
            # 只写核心逻辑，返回结果 dict
            ...
    """

    def decorator(core_func):
        @wraps(core_func)
        def wrapper(state: dict) -> dict:
            from . import check_abort

            abort = check_abort(state)
            if abort is not None:
                return abort

            print(f"[LOG] [Node] {step_name}_node 入口")
            _emit_event(state, step_name, "running", running_message)

            query = state.get("query", "")
            uploaded_files = state.get("uploaded_files", [])

            try:
                result = core_func(state)
                if not isinstance(result, dict):
                    result = {"_raw_result": result}
                result.setdefault("_workflow_step_count", state.get("_workflow_step_count", 0) + 1)
                # 透传跨节点状态变量，防止被 LangGraph 状态合并丢失
                result.setdefault("_grade_loop_count", state.get("_grade_loop_count", 0))
                result.setdefault("report", state.get("report", ""))
                result.setdefault("retrieved_chunks", state.get("retrieved_chunks", []))
                result.setdefault("report", state.get("report", ""))
                result.setdefault("current_step", step_name)
                result.setdefault("query", query)
                result.setdefault("uploaded_files", uploaded_files)
                print(f"[LOG] [Node] {step_name}_node 出口")
                return result
            except Exception as e:
                print(f"[LOG] [Node] {step_name}_node 异常 — {str(e)}")
                return {
                    "current_step": step_name,
                    "query": query,
                    "uploaded_files": uploaded_files,
                    "_workflow_step_count": state.get("_workflow_step_count", 0) + 1,
                    "errors": [f"{step_name} 节点执行失败: {str(e)}"],
                }

        return wrapper

    return decorator


def _emit_event(state: dict, step: str, status: str, message: str):
    """触发步骤变更回调"""
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass