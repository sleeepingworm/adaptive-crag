"""
任务编排器。协调文件解析、工作流执行、产物管理的完整流程。
"""

import os
import json
import shutil
from datetime import datetime

from adaptive_crag.config import load_config
from adaptive_crag.ingestion import IngestionPipeline
from adaptive_crag.ingestion.doc_registry import DocRegistry
from adaptive_crag.retrieval import EmbeddingStore, BM25Store, HybridRetriever
from adaptive_crag.graph import build_workflow, create_initial_state
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

    def start_task(self, task_id: str) -> None:
        """
        启动一个任务。

        流程:
        1. 创建产物目录
        2. 解析文件建立索引
        3. 构造初始 GraphState
        4. 执行 LangGraph 工作流
        5. 更新任务状态和产物
        """
        print(f"[LOG] [Orchestrator] start_task({task_id}) 入口")
        task = SessionManager.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        # 1. 更新状态
        print(f"[LOG] [Orchestrator] 步骤1: 更新任务状态为 running")
        SessionManager.update_task(task_id, status="running")

        # 2. 创建产物目录
        print(f"[LOG] [Orchestrator] 步骤2: 创建产物目录")
        artifact_mgr = ArtifactManager(self.config.paths.artifact_dir, task_id)
        artifact_dir = artifact_mgr.ensure_dirs()
        print(f"[LOG] [Orchestrator] 产物目录: {artifact_dir}")
        SessionManager.update_task(task_id, artifact_dir=artifact_dir)

        # 3. 初始化检索器
        print(f"[LOG] [Orchestrator] 步骤3: 初始化检索器")
        self._init_retriever()

        # 4. 解析文件并建立索引
        print(f"[LOG] [Orchestrator] 步骤4: 开始解析 {len(task.uploaded_files)} 个文件")
        # BM25 是内存索引，每次任务重建（速度快，不调模型）
        self._bm25_store.clear()
        # 加载文档哈希注册表，用于检测重复上传的文档
        doc_registry = DocRegistry(self.config.paths.index_dir)
        all_chunks = []
        all_mappings = {}

        for i, file_path in enumerate(task.uploaded_files, 1):
            print(f"[LOG] [Orchestrator] 解析文件 [{i}/{len(task.uploaded_files)}]: {os.path.basename(file_path)}")
            try:
                result = self.ingestion.process(file_path)
                chunks = result["chunks"]

                if chunks:
                    # 先写入 BM25 索引（内存索引，仅当前任务有效）
                    self._bm25_store.add_chunks(chunks)

                    # 检查文件 hash，避免重复 embedding
                    file_hash = result["document"].file_hash
                    cached = doc_registry.lookup(file_hash)
                    if cached:
                        _log_event(task_id, "vector_index", "cached",
                                  f"文档 {result['document'].filename} 命中缓存，跳过 embedding")
                    else:
                        # 再尝试写入向量索引（可能因模型下载失败而跳过）
                        try:
                            self._embed_store.add_chunks(chunks)
                            doc_registry.register(
                                file_hash,
                                result["document"].doc_id,
                                result["document"].filename,
                                len(chunks),
                            )
                        except Exception as e:
                            _log_event(task_id, "vector_index", "skipped",
                                      f"向量索引跳过（{str(e)[:60]}），仅使用关键词检索")

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

        # 设置引用映射（通过 state 传递，不再用全局变量）
        print(f"[LOG] [Orchestrator] 文件解析完成，共 {len(all_chunks)} 个片段, {len(all_mappings)} 个引用映射")

        # 5. 构造初始状态
        print(f"[LOG] [Orchestrator] 步骤5: 构造 GraphState 初始状态")
        initial_state = create_initial_state(
            query=task.query,
            uploaded_files=task.uploaded_files,
        )
        # 将 retriever 和引用映射注入线程本地存储（LangGraph state 传不了自定义 key）
        from adaptive_crag.graph.nodes.common import set_current_retriever, set_current_mappings
        set_current_retriever(self._retriever)
        set_current_mappings(all_mappings)

        # 6. 注入事件回调
        def on_step_change(step, status, message, timestamp):
            _log_event(task_id, step, status, message)
            # 更新任务状态（含实时 current_step 进度）
            SessionManager.update_task(
                task_id,
                status="running" if status == "running" else task.status,
                graph_state={"current_step": step} if step else None,
            )

        callbacks = {"on_step_change": on_step_change}
        initial_state["_callbacks"] = callbacks

        # 7. 执行工作流
        print(f"[LOG] [Orchestrator] 步骤7: 开始执行 LangGraph 工作流")
        try:
            workflow = build_workflow()
            final_state = workflow.invoke(initial_state)
            print(f"[LOG] [Orchestrator] 工作流执行完毕")

            # 8. 保存结果
            print(f"[LOG] [Orchestrator] 步骤8: 保存报告和产物")
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
            errors = final_state.get("errors", [])
            # abort 终止的任务标记为 failed，带错误信息
            if errors and any("自动终止" in str(e) for e in errors):
                task_status = "failed"
                error_msg = errors[0] if isinstance(errors, list) else str(errors)
                print(f"[LOG] [Orchestrator] 任务被 abort 终止: {error_msg}")
            else:
                task_status = "completed" if completed else "failed"

            print(f"[LOG] [Orchestrator] 任务结束 — status={task_status}, completed={completed}")

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
            print(f"[LOG] [Orchestrator] 工作流异常: {str(e)}")
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
