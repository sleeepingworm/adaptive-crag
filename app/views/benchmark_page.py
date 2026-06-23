"""
Benchmark 跑分页面：加载测试集，运行跑分引擎，展示对比结果。
"""

import streamlit as st
import pandas as pd

from adaptive_crag.evaluation.test_suite import TestSuite
from adaptive_crag.evaluation.runner import BenchmarkRunner
from adaptive_crag.evaluation.scorers import Scorer
from adaptive_crag.evaluation.comparators import Comparator

CATEGORY_MAP = {
    "全部": None,
    "文献事实问答": "literature",
    "精确术语检索": "term",
    "跨文档综合": "cross_doc",
    "表格数据分析": "data_analysis",
    "代码自修复": "repair",
}

SYSTEM_MAP = {
    "自适应 CRAG（完整）": "adaptive_crag",
    "传统 RAG（仅检索）": "traditional_rag",
    "裸模型（无检索）": "bare_llm",
}

SYSTEM_LABEL = {v: k for k, v in SYSTEM_MAP.items()}


def render_benchmark_page():
    """渲染 Benchmark 页面"""
    print("[LOG] [BenchmarkPage] render_benchmark_page() 入口")
    st.header("性能评测")
    st.caption("评估系统在黄金测试集上的表现")

    # ---- 初始化 session_state ----
    if "bench_category" not in st.session_state:
        st.session_state.bench_category = "全部"
    if "bench_system" not in st.session_state:
        st.session_state.bench_system = "裸模型（无检索）"
    if "bench_results" not in st.session_state:
        st.session_state.bench_results = {}
    if "bench_ran" not in st.session_state:
        st.session_state.bench_ran = False

    # ---- 加载测试集 ----
    suite = TestSuite("")
    cases = suite.load_all()
    stats = suite.get_stats()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("评测配置")
        st.session_state.bench_category = st.selectbox(
            "测试集",
            list(CATEGORY_MAP.keys()),
            key="bench_category_select",
        )
        st.session_state.bench_system = st.selectbox(
            "系统类型",
            list(SYSTEM_MAP.keys()),
            key="bench_system_select",
        )

    with col2:
        st.subheader("测试集统计")
        st.metric("总测试题数", stats["total"])
        for cat, count in sorted(stats.get("categories", {}).items()):
            label = {v: k for k, v in CATEGORY_MAP.items() if v}.get(cat, cat)
            st.metric(label, count)

    # ---- 开始跑分 ----
    if st.button("开始跑分", type="primary"):
        print("[LOG] [BenchmarkPage] 点击「开始跑分」按钮")
        _run_benchmark(suite, cases)

    # ---- 展示结果 ----
    if st.session_state.bench_ran:
        _show_results()

    # ---- 系统差异说明 ----
    st.divider()
    st.subheader("系统差异")
    st.markdown("""
    | 维度 | 裸模型 | 传统 RAG | 自适应 CRAG |
    |------|--------|----------|-------------|
    | 检索方式 | 无 | 仅向量检索 | 向量 + BM25 + Rerank |
    | 证据评级 | 无 | 无 | 有（不合格则联网补偿） |
    | 代码执行 | 无 | 无 | 沙箱执行 |
    | 自修复 | 无 | 无 | 失败重试 3 次 |
    | 报告引用 | 无 | 有 | 有 + 引用校验 |
    """)


def _run_benchmark(suite: TestSuite, cases: list):
    """执行跑分，结果写入 session_state"""
    category_key = CATEGORY_MAP[st.session_state.bench_category]
    system_key = SYSTEM_MAP[st.session_state.bench_system]

    # 筛选测试题
    if category_key:
        filtered = [c for c in cases if c.category == category_key]
    else:
        filtered = cases

    if not filtered:
        st.warning("没有匹配的测试题")
        return

    st.info(f"正在运行 {SYSTEM_LABEL[system_key]}，共 {len(filtered)} 题...")
    print(f"[LOG] [BenchmarkPage] 开始跑分 — system={system_key}, cases={len(filtered)}")

    progress_bar = st.progress(0)
    status_text = st.empty()

    config = {"system_type": system_key}
    runner = BenchmarkRunner(config)

    results = []
    total = len(filtered)

    for i, case in enumerate(filtered):
        status_text.text(f"[{i + 1}/{total}] {case.question[:50]}...")
        result = runner.run_single(case)
        results.append(result)
        progress_bar.progress((i + 1) / total)

    status_text.text("跑分完成")
    print(f"[LOG] [BenchmarkPage] 跑分完成 — success={sum(1 for r in results if r['success'])}/{total}")

    # 存到 session_state
    st.session_state.bench_results[system_key] = results
    st.session_state.bench_ran = True
    st.rerun()


def _show_results():
    """展示跑分结果"""
    all_results = st.session_state.bench_results
    if not all_results:
        return

    st.divider()
    st.subheader("跑分结果")

    # 按系统展示汇总
    for system_key, results in all_results.items():
        summary = Scorer.summarize(results)
        with st.expander(f"{SYSTEM_LABEL.get(system_key, system_key)} — {summary['total_cases']} 题", expanded=True):
            _render_summary_table(summary)

    # 多系统对比
    if len(all_results) >= 2:
        st.subheader("系统对比")
        comparator = Comparator()
        for system_key, results in all_results.items():
            comparator.add_result(system_key, results)

        try:
            df = comparator.export_to_dataframe()
            if df is not None:
                st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception:
            pass

        comp = comparator.compare()
        improvements = comp.get("improvement", {})
        if improvements:
            for label, metrics in improvements.items():
                label_disp = "vs 裸模型" if label == "vs_bare" else "vs 传统 RAG"
                st.caption(f"自适应 CRAG {label_disp} 的提升：")
                for metric, value in metrics.items():
                    st.write(f"- {_metric_label(metric)}: {value}")

    # 逐题详情
    st.subheader("逐题详情")
    for system_key, results in all_results.items():
        with st.expander(f"{SYSTEM_LABEL.get(system_key, system_key)} 逐题结果"):
            for r in results:
                status = "PASS" if r["success"] else "FAIL"
                st.caption(f"[{status}] {r['case_id']}: {r['question'][:60]}")


def _render_summary_table(summary: dict):
    """渲染汇总指标表格"""
    rows = [
        ("总题数", summary.get("total_cases", 0), ""),
        ("端到端成功率", f"{summary.get('end_to_end_success_rate', 0):.0%}", ""),
        ("证据命中率", f"{summary.get('evidence_hit_rate', 0):.0%}", ""),
        ("引用准确率", f"{summary.get('citation_accuracy', 0):.0%}", ""),
        ("平均延迟", f"{summary.get('avg_latency_ms', 0):.0f} ms", ""),
        ("平均 Token", f"{summary.get('avg_token_usage', 0):.0f}", ""),
        ("自修复成功率", f"{summary.get('repair_success_rate', 0):.0%}", ""),
        ("联网搜索准确率", f"{summary.get('web_search_trigger_accuracy', 0):.0%}", ""),
    ]
    df = pd.DataFrame(rows, columns=["指标", "数值", "备注"])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _metric_label(key: str) -> str:
    """指标 key 转中文标签"""
    m = {
        "end_to_end_success_rate": "端到端成功率",
        "evidence_hit_rate": "证据命中率",
        "citation_accuracy": "引用准确率",
        "avg_latency_ms": "平均延迟",
        "avg_token_usage": "Token 消耗",
    }
    return m.get(key, key)