"""
Adaptive CRAG - 自适应修正型检索增强生成系统
Streamlit 主入口。
"""

import streamlit as st

st.set_page_config(
    page_title="智能文献分析系统",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 导入页面模块
from app.views.upload_page import render_upload_page
from app.views.task_page import render_task_page
from app.views.report_page import render_report_page
from app.views.benchmark_page import render_benchmark_page


def main():
    print("[LOG] [App] main() 入口 — 渲染 Streamlit 主页面")
    # 侧边栏
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
        st.title("自适应 CRAG")
        st.caption("自适应修正型检索增强生成系统")
        st.divider()

        # 任务列表
        st.subheader("📋 任务列表")
        _render_task_list()

        st.divider()
        st.caption("v0.1.0 | 基于 LangGraph + ChromaDB")

    # 主区域 —— 使用 radio 实现可编程切换的标签页
    tab_names = ["上传与任务", "任务看板", "报告", "性能评测"]

    # 处理来自子页面的切换请求（用中间变量，避免直接修改 widget key）
    if st.session_state.get("_switch_to_report"):
        st.session_state.tab_nav = "报告"
        st.session_state._switch_to_report = False
    if st.session_state.get("_switch_to_upload"):
        st.session_state.tab_nav = "上传与任务"
        st.session_state._switch_to_upload = False

    selected_tab = st.radio(
        "导航",
        tab_names,
        key="tab_nav",
        horizontal=True,
        label_visibility="collapsed",
    )
    tab_index = tab_names.index(selected_tab)

    if tab_index == 0:
        render_upload_page()
    elif tab_index == 1:
        render_task_page()
    elif tab_index == 2:
        render_report_page()
    elif tab_index == 3:
        render_benchmark_page()


def _render_task_list():
    """侧边栏任务列表"""
    print("[LOG] [App] _render_task_list() — 刷新侧边栏任务列表")
    from adaptive_crag.application.session_manager import SessionManager

    session = SessionManager.get_session()
    tasks = list(session.tasks.values())

    if not tasks:
        st.info("暂无任务")
        return

    for task in tasks[-5:]:  # 显示最近 5 个
        status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "🚫",
        }
        icon = status_icons.get(task.status, "📝")
        label = f"{icon} {task.query[:30]}..."

        if st.button(label, key=f"sidebar_task_{task.task_id}", use_container_width=True):
            print(f"[LOG] [App] 点击侧边栏任务: {task.task_id} — 切换到该任务")
            SessionManager.set_current_task(task.task_id)
            st.rerun()


if __name__ == "__main__":
    main()
