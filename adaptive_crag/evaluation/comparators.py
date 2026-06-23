"""
对照实验分析器。对比三组系统在同一测试集上的表现。
"""


class Comparator:
    """对照实验分析器"""

    def __init__(self):
        self.results: dict[str, list[dict]] = {}

    def add_result(self, system_type: str, results: list[dict]):
        self.results[system_type] = results

    def compare(self) -> dict:
        """输出对比数据"""
        from .scorers import Scorer

        systems = list(self.results.keys())
        metrics = ["end_to_end_success_rate", "evidence_hit_rate", "citation_accuracy",
                   "avg_latency_ms", "avg_token_usage"]

        data = {}
        for system in systems:
            summary = Scorer.summarize(self.results[system])
            data[system] = [summary.get(m, 0) for m in metrics]

        # 计算改进百分比
        improvement = {}
        if "adaptive_crag" in data and "bare_llm" in data:
            adaptive = data["adaptive_crag"]
            bare = data["bare_llm"]
            improvements = {}
            for i, m in enumerate(metrics):
                if bare[i] > 0:
                    pct = (adaptive[i] - bare[i]) / bare[i] * 100
                    improvements[m] = f"+{pct:.0f}%" if pct > 0 else f"{pct:.0f}%"
            improvement["vs_bare"] = improvements

        if "adaptive_crag" in data and "traditional_rag" in data:
            adaptive = data["adaptive_crag"]
            trad = data["traditional_rag"]
            improvements = {}
            for i, m in enumerate(metrics):
                if trad[i] > 0:
                    pct = (adaptive[i] - trad[i]) / trad[i] * 100
                    improvements[m] = f"+{pct:.0f}%" if pct > 0 else f"{pct:.0f}%"
            improvement["vs_traditional"] = improvements

        return {
            "metrics": metrics,
            **data,
            "improvement": improvement,
        }

    def export_to_dataframe(self):
        """返回 pandas DataFrame"""
        try:
            import pandas as pd
            data = self.compare()
            df_data = {"指标": ["端到端成功率", "证据命中率", "引用准确率", "平均延迟(ms)", "Token消耗"]}
            for system in self.results.keys():
                label_map = {
                    "bare_llm": "裸模型",
                    "traditional_rag": "传统 RAG",
                    "adaptive_crag": "自适应 CRAG",
                }
                label = label_map.get(system, system)
                df_data[label] = data.get(system, [])
            return pd.DataFrame(df_data)
        except ImportError:
            return None
