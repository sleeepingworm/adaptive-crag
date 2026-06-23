# 模块说明书：Benchmark 评测层 (evaluation)

## 所属层级
评测层（独立于主流程）

## 目标目录
`adaptive_crag/evaluation/`

生成文件：
```
adaptive_crag/evaluation/
    __init__.py             # 导出 BenchmarkRunner
    test_suite.py           # 黄金测试集
    runner.py               # 跑分引擎
    scorers.py              # 评分器
    comparators.py          # 对照实验
    sample_questions.py     # 30-50 道样例（初始数据）
```

## 依赖模块

- **必须先生成**：`01_schema`（使用 BenchmarkCase, BenchmarkResult）
- **依赖全部主流程模块才能跑**：需要完整的 graph、tools、agents、reporting 等模块
- **可选**：`11_ui`（Benchmark 页面展示结果）

## 职责边界

**做：**
- 管理黄金测试集（加载、筛选）
- 对每个测试题运行被测系统
- 记录每题的运行指标
- 计算汇总指标
- 支持三组对照：裸模型、传统 RAG、自适应 CRAG
- 输出对比数据（用于图表展示）

**不做：**
- 不修改主流程代码
- 不影响主流程运行状态
- 不修改测试集数据（仅读取）
- 不自动优化参数

## 核心接口

### test_suite.py

```python
class TestSuite:
    """
    黄金测试集管理器。从 JSON/CSV 文件加载测试样例。
    """

    def __init__(self, data_path: str):
        """
        data_path: 测试集 JSON 文件路径
        """

    def load_all(self) -> list[BenchmarkCase]:
        """加载全部测试题"""

    def filter_by_category(self, category: str) -> list[BenchmarkCase]:
        """
        按类别筛选:
        - "literature": 文献事实问答
        - "term": 精确术语检索
        - "cross_doc": 跨文档综合
        - "data_analysis": 表格数据分析
        - "repair": 代码自修复
        - "web_compensate": 联网补偿
        """

    def get_stats(self) -> dict:
        """返回测试集统计信息：总数、各类别数量"""
```

### runner.py

```python
class BenchmarkRunner:
    """
    跑分引擎。对测试集逐个执行被测系统，记录指标。
    """

    def __init__(self, config: dict):
        """
        config:
            system_type: str   # "bare_llm" | "traditional_rag" | "adaptive_crag"
            llm_config: dict   # LLM 配置
            retrieval_config: dict | None
            sandbox_config: dict | None
        """

    def run_single(self, case: BenchmarkCase) -> dict:
        """
        运行单个测试题。

        返回:
        {
            "case_id": str,
            "question": str,
            "system_type": str,
            "success": bool,
            "total_time_ms": int,
            "token_count": int,
            "evidence_hit": bool,           # 是否命中期望证据
            "citation_accuracy": float,     # 引用准确率
            "retry_count": int,             # 重试次数
            "output": str,                  # 系统输出内容
            "errors": list[str],
        }
        """

    def run_all(self, cases: list[BenchmarkCase]) -> list[dict]:
        """
        运行全部测试题。

        实现:
        - 带进度条（tqdm）
        - 每 5 题保存一次中间结果（防崩溃丢数据）
        - 超时控制：每题最大 120 秒
        """
```

### scorers.py

```python
class Scorer:
    """
    评分器。计算各种指标。
    """

    @staticmethod
    def end_to_end_success(results: list[dict]) -> float:
        """
        端到端成功率 = 成功的题 / 总题数
        成功的定义：系统完成了生成报告的全部流程，
        且报告包含有效内容（不是空或报错）。
        """

    @staticmethod
    def evidence_hit_rate(results: list[dict]) -> float:
        """
        证据命中率 = 命中期+望证据的题 / 相关题数
        """

    @staticmethod
    def citation_accuracy(results: list[dict]) -> float:
        """
        引用准确率 = 有效引用 / 总引用数
        有效引用指能反查到原文的引用。
        """

    @staticmethod
    def avg_latency(results: list[dict]) -> float:
        """平均延迟（毫秒）"""

    @staticmethod
    def avg_token_usage(results: list[dict]) -> float:
        """平均 Token 消耗"""

    @staticmethod
    def repair_success_rate(results: list[dict]) -> float:
        """
        自修复成功率 = 修复后成功的题 / 需要修复的题数
        只有 adaptive_crag 系统有此指标。
        """

    @staticmethod
    def web_search_trigger_accuracy(results: list[dict]) -> float:
        """
        联网搜索触发准确率 = 正确触发联网的题 / 应该触发联网的题数
        """

    @staticmethod
    def summarize(results: list[dict]) -> dict:
        """
        返回所有指标的汇总 dict。
        {
            "total_cases": 50,
            "end_to_end_success_rate": 0.82,
            "evidence_hit_rate": 0.91,
            "citation_accuracy": 0.88,
            "avg_latency_ms": 12300,
            "avg_token_usage": 45000,
            "repair_success_rate": 0.75,
            "web_search_trigger_accuracy": 0.83
        }
        """
```

### comparators.py

```python
class Comparator:
    """
    对照实验分析器。对比三组系统在同一测试集上的表现。
    """

    def __init__(self):
        self.results: dict[str, list[dict]] = {}  # {"bare_llm": [...], "traditional_rag": [...], "adaptive_crag": [...]}

    def add_result(self, system_type: str, results: list[dict]):
        self.results[system_type] = results

    def compare(self) -> dict:
        """
        输出对比数据:

        {
            "metrics": ["端到端成功率", "证据命中率", "引用准确率", "平均延迟", "Token消耗"],
            "bare_llm":  [0.45, 0.30, 0.20, 5000, 30000],
            "traditional_rag": [0.65, 0.70, 0.60, 8000, 40000],
            "adaptive_crag": [0.82, 0.91, 0.88, 12300, 45000],
            "improvement": {
                "vs_bare": {"end_to_end": "+82%", "evidence": "+203%", ...},
                "vs_traditional": {"end_to_end": "+26%", "evidence": "+30%", ...}
            }
        }
        """

    def export_to_dataframe(self) -> "pd.DataFrame":
        """返回 pandas DataFrame，可直接用于图表展示"""
```

## 黄金测试集样例 (sample_questions.py)

```python
# 每个类别至少 8-10 题

LITERATURE_QUESTIONS = [
    {
        "case_id": "lit_001",
        "question": "根据上传的论文，Transformer 的核心创新是什么？",
        "expected_evidence": ["self-attention", "multi-head attention"],
        "expected_sources": ["attention_is_all_you_need.pdf"],
        "category": "literature",
        "scoring_rules": {"requires_citation": True, "expected_page": True}
    },
    # ... 更多
]

TERM_QUESTIONS = [
    {
        "case_id": "term_001",
        "question": "cv2.imshow() 函数的第一个参数是什么？",
        "expected_evidence": ["window name", "窗口名称"],
        "expected_sources": ["opencv_docs.pdf"],
        "category": "term",
        "scoring_rules": {"requires_exact_match": True}
    },
    # ... 更多
]

CROSS_DOC_QUESTIONS = [
    {
        "case_id": "cross_001",
        "question": "对比论文 A 和论文 B 对学习率调度策略的不同观点",
        "expected_evidence": ["learning rate schedule"],
        "expected_sources": ["paper_a.pdf", "paper_b.pdf"],
        "category": "cross_doc",
        "scoring_rules": {"requires_multi_source": True}
    },
    # ... 更多
]

DATA_ANALYSIS_QUESTIONS = [
    {
        "case_id": "data_001",
        "question": "分析销售数据中每个季度的平均销售额，并绘制折线图",
        "expected_evidence": ["quarter", "average sales"],
        "expected_sources": ["sales_data.csv"],
        "category": "data_analysis",
        "scoring_rules": {"requires_chart": True, "requires_code": True}
    },
    # ... 更多
]

REPAIR_QUESTIONS = [
    {
        "case_id": "repair_001",
        "question": "计算数据集中每个类别的数量并绘制柱状图（故意用错列名）",
        "expected_evidence": [],
        "expected_sources": ["sample_data.csv"],
        "category": "repair",
        "scoring_rules": {"requires_repair": True}
    },
    # ... 更多
]
```

## 测试集 JSON 文件结构

```json
[
    {
        "case_id": "lit_001",
        "question": "根据上传的论文，Transformer 的核心创新是什么？",
        "expected_evidence": ["self-attention", "multi-head attention"],
        "expected_sources": ["attention_is_all_you_need.pdf"],
        "category": "literature",
        "scoring_rules": {"requires_citation": true, "expected_page": true},
        "setup_files": ["attention_is_all_you_need.pdf"]   # 执行前需要上传到系统的文件
    }
]
```

## 三组对照系统的差异

| 维度 | 裸模型 | 传统 RAG | 自适应 CRAG |
|------|--------|----------|-------------|
| 检索方式 | 无 | 仅向量检索 | 向量 + BM25 + Rerank |
| 证据评级 | 无 | 无 | 有（不合格则联网补偿） |
| 代码执行 | 无 | 无 | 沙箱执行 |
| 自修复 | 无 | 无 | 有（失败重试 3 次） |
| 报告引用 | 无 | 有 | 有 + 引用校验 |

传统 RAG 实现方式：在 `runner.py` 中构造一个简化版 graph，只走 retrieve -> report 路径。

## 与上下游模块的对接

- **上游调用方**：Benchmark 页面（用户点击跑分时触发）
- **下游依赖**：完整的主流程模块组（graph, tools, agents, retrieval, reporting 等）
- **数据流向**：`用户 -> BenchmarkRunner.run_all() -> 每个 case 调用主流程 -> 记录指标 -> comparator.compare() -> UI 图表`

## 测试要点

- 空测试集能返回空的汇总结果
- 单个测试用例能正确记录指标
- Scorer.summarize 输出字段完整
- Comparator.compare 输出的指标图数据格式正确
- 每个类别的测试题至少有 1 题功能正常