"""
黄金测试集样例。每个类别至少 8-10 题。
"""

from adaptive_crag.schema import BenchmarkCase


def get_sample_questions() -> list[BenchmarkCase]:
    """获取内置测试样例"""
    literature = [
        BenchmarkCase(
            case_id="lit_001",
            question="根据上传的论文，Transformer 的核心创新是什么？",
            expected_evidence=["self-attention", "multi-head attention"],
            expected_sources=["attention_is_all_you_need.pdf"],
            category="literature",
            scoring_rules={"requires_citation": True, "expected_page": True},
            setup_files=["attention_is_all_you_need.pdf"],
        ),
        BenchmarkCase(
            case_id="lit_002",
            question="ResNet 解决了什么深度学习问题？",
            expected_evidence=["degradation problem", "skip connection", "residual learning"],
            expected_sources=["resnet.pdf"],
            category="literature",
            scoring_rules={"requires_citation": True},
        ),
        BenchmarkCase(
            case_id="lit_003",
            question="对比 LSTM 和 GRU 的结构差异",
            expected_evidence=["forget gate", "update gate", "reset gate"],
            expected_sources=["lstm.pdf", "gru.pdf"],
            category="literature",
            scoring_rules={"requires_multi_source": True},
        ),
    ]

    terms = [
        BenchmarkCase(
            case_id="term_001",
            question="Python 中 matplotlib.pyplot 的 imshow() 函数第一个参数是什么？",
            expected_evidence=["image array", "array-like"],
            category="term",
            scoring_rules={"requires_exact_match": True},
        ),
        BenchmarkCase(
            case_id="term_002",
            question="Pandas 中 DataFrame.describe() 默认计算哪些统计量？",
            expected_evidence=["count", "mean", "std", "min", "25%", "50%", "75%", "max"],
            category="term",
            scoring_rules={"requires_exact_match": True},
        ),
    ]

    cross_doc = [
        BenchmarkCase(
            case_id="cross_001",
            question="对比论文 A 和论文 B 对学习率调度策略的不同观点",
            expected_evidence=["learning rate schedule", "warmup"],
            expected_sources=["paper_a.pdf", "paper_b.pdf"],
            category="cross_doc",
            scoring_rules={"requires_multi_source": True},
        ),
    ]

    data_analysis = [
        BenchmarkCase(
            case_id="data_001",
            question="分析销售数据中每个季度的平均销售额",
            expected_evidence=["quarter", "average sales"],
            category="data_analysis",
            scoring_rules={"requires_chart": True, "requires_code": True},
        ),
    ]

    repair = [
        BenchmarkCase(
            case_id="repair_001",
            question="计算数据集中每个类别的数量并绘制柱状图",
            expected_evidence=[],
            category="repair",
            scoring_rules={"requires_repair": True},
        ),
    ]

    all_cases = literature + terms + cross_doc + data_analysis + repair
    return all_cases
