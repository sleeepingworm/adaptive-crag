"""
任务看板页面：展示任务执行进度。
"""

import time
import streamlit as st
from adaptive_crag.application.session_manager import SessionManager

# 步骤定义（顺序决定进度百分比）
STEPS = [
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
STEP_KEYS = [s[0] for s in STEPS]


def _calc_progress(task) -> float:
    """根据当前步骤计算 0.0~1.0 的进度"""
    if task.status == "completed":
        return 1.0
    if task.status in ("failed", "cancelled"):
        return 0.0

    step = ""
    if task.graph_state:
        step = task.graph_state.get("current_step", "")
    if step in STEP_KEYS:
        idx = STEP_KEYS.index(step)
        return (idx + 1) / len(STEP_KEYS)
    return 0.0


def _get_status_label(status: str) -> str:
    labels = {
        "pending": "等待中",
        "running": "执行中",
        "completed": "已完成",
        "failed": "失败",
        "cancelled": "已取消",
    }
    return labels.get(status, status)


def _get_status_color(status: str) -> str:
    colors = {
        "pending": "🔵",
        "running": "🟡",
        "completed": "🟢",
        "failed": "🔴",
        "cancelled": "⚪",
    }
    return colors.get(status, "⚪")


def render_task_page():
    """渲染任务看板页面"""
    print("[LOG] [TaskPage] render_task_page() 入口")
    st.header("📊 任务看板")

    task_id = st.session_state.get("current_task_id")
    if not task_id:
        st.info("💡 请先在「上传与任务」页面创建分析任务")
        return

    task = SessionManager.get_task(task_id)
    if not task:
        st.warning("任务不存在")
        return

    # ---- 进度条 ----
    progress = _calc_progress(task)
    st.progress(progress, text=f"整体进度 {int(progress * 100)}%")

    # ---- 状态卡片行 ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("状态", f"{_get_status_color(task.status)} {_get_status_label(task.status)}")
    with col2:
        st.metric("任务 ID", task.task_id[:12] + "...")
    with col3:
        if task.created_at:
            st.metric("创建时间", task.created_at[11:19])
    with col4:
        current_step = task.graph_state.get("current_step", "") if task.graph_state else ""
        st.metric("当前步骤", current_step or "-")

    # ---- 步骤明细 ----
    st.subheader("执行进度")

    current_step_name = task.graph_state.get("current_step", "") if task.graph_state else ""
    completed_steps = []

    if current_step_name in STEP_KEYS:
        idx = STEP_KEYS.index(current_step_name)
        completed_steps = STEP_KEYS[:idx]
    elif task.status == "completed":
        completed_steps = STEP_KEYS

    for step_key, step_label in STEPS:
        if step_key in completed_steps:
            st.success(f"✅ {step_label}")
        elif step_key == current_step_name:
            if task.status == "failed":
                st.error(f"❌ {step_label}")
            else:
                st.info(f"🔄 {step_label}")
        else:
            st.text(f"⏳ {step_label}")

    # ---- 事件日志 ----
    st.subheader("执行日志")
    if task.events:
        for event in task.events[-15:]:  # 最近 15 条
            ts = event.get("timestamp", "")[11:19] if event.get("timestamp") else ""
            msg = event.get("message", "")
            ev_status = event.get("status", "")
            if ev_status == "completed":
                icon = "✅"
            elif ev_status == "running":
                icon = "🔄"
            else:
                icon = "❌"
            st.caption(f"{icon} [{ts}] {msg}")
    else:
        st.caption("暂无日志")

    # ---- 错误信息 ----
    if task.error:
        st.error(f"错误: {task.error}")

    # ---- 自动刷新（仅 running） ----
    if task.status == "running":
        st.button("🔄 刷新状态")
        print(f"[LOG] [TaskPage] 任务 {task_id} 状态=running, 自动刷新中...")
        last_rerun = st.session_state.get("_last_task_rerun", time.time())
        now = time.time()
        if now - last_rerun >= 2.0:
            st.session_state["_last_task_rerun"] = now
            st.rerun()
        else:
            last_msg = task.events[-1].get("message", "") if task.events else "处理中..."
            st.caption(f"⏳ {last_msg}")
            st.caption("(自动刷新中...)")

    # ---- 查看报告 / 重试按钮 ----
    if task.status == "completed":
        if st.button("📄 查看报告", type="primary"):
            print(f"[LOG] [TaskPage] 点击「查看报告」— 跳转到报告页面")
            st.session_state["_switch_to_report"] = True
            st.rerun()
    elif task.status == "failed":
        st.error(f"任务执行失败，请检查日志后重试")
        if st.button("🔄 返回上传页重新开始"):
            st.session_state["_switch_to_upload"] = True
            st.rerun()