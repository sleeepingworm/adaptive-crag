"""
黄金测试集样例。使用真实可用的论文文件。
每个类别问题针对 CRAG 论文内容设计，setup_files 指向实际存在的文件。
"""

import os
from adaptive_crag.schema import BenchmarkCase

# 真实论文文件路径（相对于项目根目录）
CRAG_PAPER = "data/uploads/CRAG_paper.pdf"


def _paper_path() -> list[str]:
    """返回 CRAG 论文路径（仅当文件存在时）"""
    if os.path.exists(CRAG_PAPER):
        return [CRAG_PAPER]
    # 尝试绝对路径
    alt = os.path.join(os.path.dirname(__file__), "..", "..", CRAG_PAPER)
    alt = os.path.abspath(alt)
    if os.path.exists(alt):
        return [alt]
    return []


def get_sample_questions() -> list[BenchmarkCase]:
    """获取内置测试样例"""
    paper = _paper_path()

    # ---- 文献问答类 ----
    literature = [
        BenchmarkCase(
            case_id="lit_001",
            question="根据 CRAG 论文，其核心创新机制是什么？",
            expected_evidence=["retrieval evaluator", "corrective", "web search"],
            expected_sources=[CRAG_PAPER],
            category="literature",
            scoring_rules={"requires_citation": True},
            setup_files=paper,
        ),
        BenchmarkCase(
            case_id="lit_002",
            question="CRAG 的 retrieval evaluator 如何判断检索质量？",
            expected_evidence=["confidence", "relevance", "retrieval"],
            expected_sources=[CRAG_PAPER],
            category="literature",
            scoring_rules={"requires_citation": True},
            setup_files=paper,
        ),
        BenchmarkCase(
            case_id="lit_003",
            question="CRAG 论文中 web search 在什么情况下被触发？",
            expected_evidence=["web search", "insufficient", "trigger"],
            expected_sources=[CRAG_PAPER],
            category="literature",
            scoring_rules={"requires_citation": True},
            setup_files=paper,
        ),
        BenchmarkCase(
            case_id="lit_004",
            question="CRAG 与标准 RAG 和 Self-RAG 的主要区别是什么？",
            expected_evidence=["retrieval", "evaluator", "corrective", "self"],
            expected_sources=[CRAG_PAPER],
            category="literature",
            scoring_rules={"requires_citation": True},
            setup_files=paper,
        ),
    ]

    # ---- 术语检索类 ----
    terms = [
        BenchmarkCase(
            case_id="term_001",
            question="CRAG 论文中 'retrieval evaluator' 的定义是什么？",
            expected_evidence=["retrieval evaluator", "confidence"],
            category="term",
            scoring_rules={"requires_exact_match": True},
            setup_files=paper,
        ),
        BenchmarkCase(
            case_id="term_002",
            question="CRAG 论文中 'corrective' 指的是什么？",
            expected_evidence=["corrective", "knowledge", "refinement"],
            category="term",
            scoring_rules={"requires_exact_match": True},
            setup_files=paper,
        ),
    ]

    # ---- 跨文档综合类（单文档变体：同一论文的不同方面对比） ----
    cross_doc = [
        BenchmarkCase(
            case_id="cross_001",
            question="对比 CRAG 中静态检索和自适应检索的性能差异",
            expected_evidence=["static", "adaptive", "retrieval", "performance"],
            expected_sources=[CRAG_PAPER],
            category="cross_doc",
            scoring_rules={"requires_multi_source": False},
            setup_files=paper,
        ),
    ]

    # ---- 数据分析类（论文实验数据） ----
    data_analysis = [
        BenchmarkCase(
            case_id="data_001",
            question="分析 CRAG 论文中的实验评估指标和对比结果",
            expected_evidence=["accuracy", "evaluation", "dataset", "result"],
            category="data_analysis",
            scoring_rules={"requires_chart": False, "requires_code": False},
            setup_files=paper,
        ),
    ]

    # ---- 代码自修复类（裸模型可回答） ----
    repair = [
        BenchmarkCase(
            case_id="repair_001",
            question="如果你要用 Python 实现 CRAG 的 retrieval evaluator，大致需要哪些步骤？",
            expected_evidence=[],
            category="repair",
            scoring_rules={"requires_repair": False},
            setup_files=[],  # 裸模型可回答，不需要文件
        ),
    ]

    all_cases = literature + terms + cross_doc + data_analysis + repair
    return all_cases