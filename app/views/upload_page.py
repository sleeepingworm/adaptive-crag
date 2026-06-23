"""
上传页面：文件上传与任务创建。
"""

import os
import threading
import streamlit as st
from adaptive_crag.application.session_manager import SessionManager
from adaptive_crag.application.task_orchestrator import TaskOrchestrator


def render_upload_page():
    """渲染上传页面"""
    print("[LOG] [UploadPage] render_upload_page() 入口")
    st.header("📤 上传文件并创建分析任务")

    # 初始化 session state
    if "uploaded_files_cache" not in st.session_state:
        st.session_state.uploaded_files_cache = []
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = TaskOrchestrator()

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("上传文件")
        uploaded_files = st.file_uploader(
            "支持 PDF、TXT、Markdown、Word、CSV、Excel 格式",
            type=["pdf", "txt", "md", "docx", "csv", "xlsx"],
            accept_multiple_files=True,
            help="单文件上限 50MB，总上传上限 200MB",
        )

        if uploaded_files:
            print(f"[LOG] [UploadPage] 用户选择了 {len(uploaded_files)} 个文件: {[f.name for f in uploaded_files]}")
            st.success(f"已选择 {len(uploaded_files)} 个文件")

            # 显示已上传文件列表
            for f in uploaded_files:
                file_size = f.size / 1024
                size_str = f"{file_size:.1f} KB" if file_size < 1024 else f"{file_size / 1024:.1f} MB"
                st.text(f"📄 {f.name} ({size_str})")

    with col2:
        st.subheader("创建任务")

        # 任务输入
        query = st.text_area(
            "输入你的研究问题或分析需求",
            placeholder="例如：分析这些文献中关于 Transformer 的核心观点，并对比不同论文的结论",
            height=150,
        )

        # 保存文件并开始
        if st.button("🚀 开始分析", type="primary", use_container_width=True,
                     disabled=not (query and uploaded_files)):
            print(f"[LOG] [UploadPage] 点击「开始分析」按钮 — query={query[:50]}..., files={len(uploaded_files)}个")
            with st.spinner("正在准备任务..."):
                # 保存文件
                from adaptive_crag.config import load_config
                config = load_config()
                session = SessionManager.get_session()
                session_id = session.session_id

                saved_paths = []
                for f in uploaded_files:
                    # 安全处理文件名：仅保留纯文件名，阻止路径穿越
                    safe_name = os.path.basename(f.name)
                    if not safe_name or safe_name != f.name:
                        st.error(f"文件名不安全: {f.name}")
                        continue
                    save_dir = os.path.join(config.paths.upload_dir, session_id)
                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, safe_name)
                    # 避免同名文件静默覆盖
                    if os.path.exists(save_path):
                        base, ext = os.path.splitext(safe_name)
                        import uuid
                        safe_name = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
                        save_path = os.path.join(save_dir, safe_name)
                    with open(save_path, "wb") as out:
                        out.write(f.getbuffer())
                    saved_paths.append(save_path)

                # 创建任务
                task_id = SessionManager.create_task(query, saved_paths)
                st.session_state["current_task_id"] = task_id

                # 后台线程执行任务（不阻塞 UI）
                orchestrator = st.session_state.orchestrator
                thread = threading.Thread(
                    target=orchestrator.start_task,
                    args=(task_id,),
                    daemon=True,
                )
                thread.start()
                print(f"[LOG] [UploadPage] 任务 {task_id} 已在后台线程启动")

                st.success(f"任务已创建: {task_id}")
                st.rerun()

        # 显示空状态
        if not query:
            st.info("💡 输入研究问题并上传相关文件，系统将自动检索、分析并生成报告")
        elif not uploaded_files:
            st.warning("请先上传文件")

    # 最近任务
    st.divider()
    st.subheader("📋 最近任务")
    tasks = SessionManager.list_tasks()
    if tasks:
        for task in reversed(tasks[-5:]):
            status_map = {
                "pending": "⏳ 等待中",
                "running": "🔄 执行中",
                "completed": "✅ 已完成",
                "failed": "❌ 失败",
                "cancelled": "🚫 已取消",
            }
            status_text = status_map.get(task.status, task.status)
            col_status, col_query, col_time = st.columns([1, 3, 2])
            with col_status:
                st.text(status_text)
            with col_query:
                st.text(task.query[:50] + "..." if len(task.query) > 50 else task.query)
            with col_time:
                st.caption(task.created_at[:19] if task.created_at else "")
    else:
        st.info("暂无任务记录")
