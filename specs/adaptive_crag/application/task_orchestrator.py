"""
任务编排器。协调文件解析、工作流执行、产物管理的完整流程。
"""

import os
import json
import shutil
from datetime import datetime

from adaptive_crag.config import load_config
from adaptive_crag.ingestion import IngestionPipeline
from adaptive_crag.retrieval import EmbeddingStore, BM25Store, HybridRetriever
from adaptive_crag.graph import build_workflow, create_initial_state
from adaptive_crag.tools.hybrid_search import set_hybrid_retriever
from adaptive_crag.tools.citation_lookup import set_citation_mappings
from .artifact_manager import ArtifactManager
from .session_manager import SessionManager


class TaskOrchestrator:
    """
    任务编排器。协调文件解析、索引构建、工作流执行的完整流程。
    """

    def __init__(self, config=None):
        self.config = config or load_config()
        self.ingestion = IngestionPipeline(max_tokens=self.config.retrieval.chunk_max_tokens)
        self._retriever = None
        self._embed_store = None
        self._bm25_store = None

    def _init_retriever(self):
        """初始化检索器（懒加载）"""
        if self._retriever is None:
            self._embed_store = EmbeddingStore(
                persist_dir=self.config.paths.chroma_persist_dir,
            )
            self._bm25_store = BM25Store()
            self._retriever = HybridRetriever(
                embed_store=self._embed_store,
                bm25_store=self._bm25_store,
                config=self.config.retrieval,
            )
            set_hybrid_retriever(self._retriever)

    def start_task(self, session, task_id: str) -> None:
        """
        启动一个任务。

        流程:
        1. 创建产物目录
        2. 解析文件建立索引
        3. 构造初始 GraphState
        4. 执行 LangGraph 工作流
        5. 更新任务状态和产物
        """
        task = session.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 1. 更新状态
        task.status = "running"
        SessionManager.update_task(task_id, status="running")

        # 2. 创建产物目录
        artifact_mgr = ArtifactManager(self.config.paths.artifact_dir, task_id)
        artifact_dir = artifact_mgr.ensure_dirs()
        SessionManager.update_task(task_id, artifact_dir=artifact_dir)

        # 3. 初始化检索器
        self._init_retriever()

        # 4. 解析文件并建立索引
        all_chunks = []
        all_mappings = {}

        for file_path in task.uploaded_files:
            try:
                result = self.ingestion.process(file_path)
                chunks = result["chunks"]

                if chunks:
                    # 写入向量和 BM25 索引
                    self._embed_store.add_chunks(chunks)
                    self._bm25_store.add_chunks(chunks)

                    # 构建引用映射
                    for c in chunks:
                        all_mappings[c.chunk_id] = {
                            "doc_id": c.doc_id,
                            "page_num": c.page_num,
                            "filename": result["document"].filename,
                            "text_snippet": c.text[:200],
                            "file_path": file_path,
                        }

                    all_chunks.extend(chunks)

                # 保存 profile
                if result.get("profile"):
                    profile_path = os.path.join(artifact_dir, "data_profile.json")
                    with open(profile_path, "w", encoding="utf-8") as f:
                        json.dump({
                            "filename": result["document"].filename,
                            "row_count": result["profile"].row_count,
                            "column_count": result["profile"].column_count,
                            "columns": result["profile"].columns,
                        }, f, ensure_ascii=False, indent=2)

                _log_event(task_id, "ingestion", "completed",
                          f"已解析文件: {os.path.basename(file_path)} ({len(chunks)} 个片段)")

            except Exception as e:
                _log_event(task_id, "ingestion", "failed",
                          f"文件解析失败: {os.path.basename(file_path)} - {str(e)}")

        # 设置引用映射
        set_citation_mappings(all_mappings)

        # 5. 构造初始状态
        initial_state = create_initial_state(
            query=task.query,
            uploaded_files=task.uploaded_files,
        )

        # 6. 注入事件回调
        def on_step_change(step, status, message, timestamp):
            _log_event(task_id, step, status, message)
            # 更新任务状态
            SessionManager.update_task(task_id, status="running" if status == "running" else task.status)

        callbacks = {"on_step_change": on_step_change}
        initial_state["_callbacks"] = callbacks

        # 7. 执行工作流
        try:
            workflow = build_workflow()
            final_state = workflow.invoke(initial_state)

            # 8. 保存结果
            report = final_state.get("report", "")
            if report:
                artifact_mgr.save_report(report)

            # 收集产物
            chart_paths = artifact_mgr.collect_charts()
            execution_result = final_state.get("execution_result")
            if execution_result and isinstance(execution_result, dict):
                gen_files = execution_result.get("generated_files", [])
                for f in gen_files:
                    if os.path.exists(f):
                        shutil.copy2(f, os.path.join(artifact_dir, "charts"))

            # 更新任务
            completed = final_state.get("completed", False)
            task_status = "completed" if completed else "failed"

            SessionManager.update_task(
                task_id,
                status=task_status,
                graph_state=final_state,
                report=report,
                completed_at=datetime.now().isoformat(),
            )

            _log_event(task_id, "workflow", "completed" if completed else "failed",
                      f"工作流执行{'完成' if completed else '失败'}")

        except Exception as e:
            SessionManager.update_task(
                task_id,
                status="failed",
                error=str(e),
                completed_at=datetime.now().isoformat(),
            )
            _log_event(task_id, "workflow", "failed", f"工作流异常: {str(e)}")

    def cancel_task(self, task_id: str) -> None:
        """取消正在执行的任务"""
        SessionManager.update_task(task_id, status="cancelled")
        _log_event(task_id, "workflow", "cancelled", "任务已被用户取消")

    def get_task_events(self, task_id: str) -> list[dict]:
        """获取任务的事件列表"""
        task = SessionManager.get_task(task_id)
        return task.events if task else []

    def get_task_status(self, task_id: str) -> dict:
        """返回当前状态的摘要"""
        task = SessionManager.get_task(task_id)
        if not task:
            return {"status": "not_found", "current_step": "", "progress": 0, "elapsed_seconds": 0}

        elapsed = 0
        if task.created_at:
            try:
                created = datetime.fromisoformat(task.created_at)
                elapsed = int((datetime.now() - created).total_seconds())
            except Exception:
                pass

        current_step = ""
        if task.graph_state:
            current_step = task.graph_state.get("current_step", "")

        return {
            "status": task.status,
            "current_step": current_step,
            "progress": _calc_progress(task.status, current_step),
            "elapsed_seconds": elapsed,
        }


def _log_event(task_id: str, step: str, status: str, message: str):
    """记录事件到任务"""
    from datetime import datetime
    event = {
        "step": step,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
    SessionManager.add_event(task_id, event)


def _calc_progress(status: str, current_step: str) -> float:
    """根据当前步骤估算进度"""
    if status == "completed":
        return 1.0
    if status == "failed" or status == "cancelled":
        return 0.0

    steps = ["init", "route", "retrieve", "grade", "web_search", "analyze",
             "code_write", "execute", "repair", "report", "validate"]
    step_progress = {
        "init": 0.0,
        "route": 0.1,
        "retrieve": 0.2,
        "grade": 0.3,
        "web_search": 0.35,
        "analyze": 0.4,
        "code_write": 0.5,
        "execute": 0.6,
        "repair": 0.65,
        "report": 0.8,
        "validate": 0.9,
    }
    return step_progress.get(current_step, 0.0)
