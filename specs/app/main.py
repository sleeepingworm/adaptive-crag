"""
Adaptive CRAG - 自适应修正型检索增强生成系统
Streamlit 主入口。
"""

import streamlit as st

st.set_page_config(
    page_title="Adaptive CRAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 导入页面模块
from app.pages.upload_page import render_upload_page
from app.pages.task_page import render_task_page
from app.pages.report_page import render_report_page
from app.pages.benchmark_page import render_benchmark_page


def main():
    # 侧边栏
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
        st.title("Adaptive CRAG")
        st.caption("自适应修正型检索增强生成系统")
        st.divider()

        # 任务列表
        st.subheader("📋 任务列表")
        _render_task_list()

        st.divider()
        st.caption("v0.1.0 | Powered by LangGraph + ChromaDB")

    # 主区域标签页
    tabs = st.tabs(["📤 上传与任务", "📊 任务看板", "📄 报告", "📈 Benchmark"])

    with tabs[0]:
        render_upload_page()

    with tabs[1]:
        render_task_page()

    with tabs[2]:
        render_report_page()

    with tabs[3]:
        render_benchmark_page()


def _render_task_list():
    """侧边栏任务列表"""
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
            SessionManager.set_current_task(task.task_id)
            st.rerun()


if __name__ == "__main__":
    main()
