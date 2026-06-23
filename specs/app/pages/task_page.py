"""
任务看板页面：展示任务执行进度。
"""

import streamlit as st
from adaptive_crag.application.session_manager import SessionManager


def render_task_page():
    """渲染任务看板页面"""
    st.header("📊 任务看板")

    task_id = st.session_state.get("current_task_id")
    if not task_id:
        st.info("💡 请先在「上传与任务」页面创建分析任务")
        return

    task = SessionManager.get_task(task_id)
    if not task:
        st.warning("任务不存在")
        return

    # 任务状态卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_color = {
            "pending": "🔵",
            "running": "🟡",
            "completed": "🟢",
            "failed": "🔴",
            "cancelled": "⚪",
        }
        st.metric("状态", f"{status_color.get(task.status, '⚪')} {task.status}")
    with col2:
        st.metric("任务 ID", task.task_id[:12] + "...")
    with col3:
        if task.created_at:
            st.metric("创建时间", task.created_at[11:19])
    with col4:
        current_step = task.graph_state.get("current_step", "") if task.graph_state else ""
        st.metric("当前步骤", current_step or "-")

    # 进度展示
    st.subheader("执行进度")

    steps = [
        ("init", "📋 任务规划"),
        ("route", "🎯 任务路由"),
        ("retrieve", "📚 文献检索"),
        ("grade", "🔍 证据评估"),
        ("web_search", "🌐 联网搜索"),
        ("analyze", "📊 分析规划"),
        ("code_write", "💻 代码生成"),
        ("execute", "⚙️ 代码执行"),
        ("repair", "🔧 代码修复"),
        ("report", "📝 报告生成"),
        ("validate", "✅ 引用校验"),
    ]

    current_step_name = task.graph_state.get("current_step", "") if task.graph_state else ""
    completed_steps = []

    # 确定已完成步骤
    step_names = [s[0] for s in steps]
    if current_step_name in step_names:
        idx = step_names.index(current_step_name)
        completed_steps = step_names[:idx]
    elif task.status == "completed":
        completed_steps = step_names

    for step_key, step_label in steps:
        if step_key in completed_steps:
            st.success(f"✅ {step_label}")
        elif step_key == current_step_name:
            st.info(f"🔄 {step_label}")
        elif task.status == "failed" and step_key == current_step_name:
            st.error(f"❌ {step_label}")
        else:
            st.text(f"⏳ {step_label}")

    # 事件日志
    st.subheader("执行日志")
    if task.events:
        for event in task.events[-10:]:  # 最近 10 条
            ts = event.get("timestamp", "")[11:19] if event.get("timestamp") else ""
            msg = event.get("message", "")
            status = event.get("status", "")
            icon = "✅" if status == "completed" else "🔄" if status == "running" else "❌"
            st.caption(f"{icon} [{ts}] {msg}")
    else:
        st.caption("暂无日志")

    # 自动刷新
    if task.status == "running":
        st.button("🔄 刷新状态", on_click=lambda: None)
        st.caption("任务执行中，请稍候...")
        st.rerun()

    # 错误信息
    if task.error:
        st.error(f"错误: {task.error}")

    if task.status in ("completed", "failed"):
        if st.button("📄 查看报告", type="primary"):
            st.session_state["active_tab"] = 2
            st.rerun()
