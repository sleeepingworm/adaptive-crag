"""
报告页面：展示报告、图表和引用信息。
"""

import os
import streamlit as st
from adaptive_crag.application.session_manager import SessionManager


def render_report_page():
    """渲染报告页面"""
    st.header("📄 研究报告")

    task_id = st.session_state.get("current_task_id")
    if not task_id:
        st.info("💡 请先完成一个分析任务")
        return

    task = SessionManager.get_task(task_id)
    if not task:
        st.warning("任务不存在")
        return

    if task.status != "completed":
        if task.status == "running":
            st.warning("⏳ 任务还在执行中，请稍候...")
            if st.button("🔄 刷新"):
                st.rerun()
        else:
            st.info("📝 任务尚未完成，无法生成报告")
        return

    # 报告内容
    if task.report:
        st.markdown(task.report)
    else:
        # 尝试从产物目录读取
        if task.artifact_dir:
            report_path = os.path.join(task.artifact_dir, "report.md")
            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as f:
                    report_content = f.read()
                st.markdown(report_content)
            else:
                st.warning("报告文件未找到")
        else:
            st.warning("报告内容为空")

    # 图表展示区
    st.divider()
    st.subheader("📊 数据图表")

    chart_paths = []
    if task.artifact_dir:
        charts_dir = os.path.join(task.artifact_dir, "charts")
        if os.path.exists(charts_dir):
            chart_paths = [
                os.path.join(charts_dir, f)
                for f in os.listdir(charts_dir)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".svg"))
            ]

    if chart_paths:
        cols = st.columns(min(len(chart_paths), 3))
        for i, chart_path in enumerate(chart_paths):
            with cols[i % 3]:
                st.image(chart_path, use_container_width=True)
    else:
        st.info("本次分析未生成图表")

    # 引用列表
    st.divider()
    st.subheader("📚 引用列表")

    citations = []
    if task.artifact_dir:
        cit_path = os.path.join(task.artifact_dir, "citations.json")
        if os.path.exists(cit_path):
            import json
            with open(cit_path, "r", encoding="utf-8") as f:
                citations = json.load(f)

    if citations:
        for i, cit in enumerate(citations, 1):
            with st.expander(f"[{i}] {cit.get('claim', '')[:80]}..."):
                st.write(f"**来源**: {cit.get('source_filename', '未知')}")
                if cit.get("page_num"):
                    st.write(f"**页码**: 第 {cit['page_num']} 页")
                st.write(f"**置信度**: {cit.get('confidence', 0):.2%}")
    else:
        st.caption("无引用信息")

    # 下载按钮
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if task.report:
            st.download_button(
                label="📥 下载 Markdown 报告",
                data=task.report,
                file_name=f"report_{task_id[:8]}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    with col2:
        if chart_paths:
            import zipfile
            import io

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in chart_paths:
                    zf.write(path, os.path.basename(path))
            buf.seek(0)

            st.download_button(
                label="📦 下载图表包 (ZIP)",
                data=buf,
                file_name=f"charts_{task_id[:8]}.zip",
                mime="application/zip",
                use_container_width=True,
            )

    with col3:
        if task.artifact_dir:
            log_path = os.path.join(task.artifact_dir, "logs", "event_log.jsonl")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    log_content = f.read()
                st.download_button(
                    label="📋 下载执行日志",
                    data=log_content,
                    file_name=f"logs_{task_id[:8]}.jsonl",
                    mime="application/jsonl",
                    use_container_width=True,
                )
