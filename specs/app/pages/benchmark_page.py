"""
Benchmark 跑分页面：展示评测配置和结果。
"""

import streamlit as st
import pandas as pd


def render_benchmark_page():
    """渲染 Benchmark 页面"""
    st.header("📈 Benchmark 评测")
    st.caption("评估系统在黄金测试集上的表现")

    # 评测配置
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("评测配置")
        test_set = st.selectbox(
            "测试集",
            ["全部", "文献事实问答", "精确术语检索", "跨文档综合", "表格数据分析", "代码自修复"],
        )
        system_type = st.selectbox(
            "系统类型",
            ["自适应 CRAG（完整）", "传统 RAG（仅检索）", "裸模型（无检索）"],
        )
        model = st.selectbox(
            "LLM 模型",
            ["gpt-4o", "gpt-4o-mini", "qwen2.5:7b", "deepseek-chat"],
        )

    with col2:
        st.subheader("测试集统计")
        st.metric("总测试题数", "50")
        st.metric("文献问答", "15")
        st.metric("术语检索", "8")
        st.metric("跨文档综合", "10")
        st.metric("数据分析", "10")
        st.metric("代码自修复", "7")

    # 开始按钮
    if st.button("🚀 开始跑分", type="primary", disabled=True):
        st.info("评测引擎开发中，敬请期待...")

    # 示例结果展示
    st.divider()
    st.subheader("📊 参考指标（目标值）")

    # 三组对照数据
    data = {
        "指标": ["端到端成功率", "证据命中率", "引用准确率", "平均延迟(ms)", "Token 消耗"],
        "裸模型": ["45%", "30%", "20%", "5,000", "30,000"],
        "传统 RAG": ["65%", "70%", "60%", "8,000", "40,000"],
        "自适应 CRAG": ["82%", "91%", "88%", "12,300", "45,000"],
    }
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 说明
    st.divider()
    st.subheader("📖 说明")
    st.markdown("""
    **三组对照系统差异：**

    | 维度 | 裸模型 | 传统 RAG | 自适应 CRAG |
    |------|--------|----------|-------------|
    | 检索方式 | 无 | 仅向量检索 | 向量 + BM25 + Rerank |
    | 证据评级 | 无 | 无 | 有（不合格则联网补偿） |
    | 代码执行 | 无 | 无 | 沙箱执行 |
    | 自修复 | 无 | 无 | 失败重试 3 次 |
    | 报告引用 | 无 | 有 | 有 + 引用校验 |
    """)
