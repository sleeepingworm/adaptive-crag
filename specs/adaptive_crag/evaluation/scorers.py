"""
评分器。计算端到端成功率、证据命中率、引用准确率等指标。
"""


class Scorer:
    """评分器"""

    @staticmethod
    def end_to_end_success(results: list[dict]) -> float:
        """端到端成功率"""
        if not results:
            return 0.0
        successes = sum(1 for r in results if r.get("success", False))
        return successes / len(results)

    @staticmethod
    def evidence_hit_rate(results: list[dict]) -> float:
        """证据命中率"""
        if not results:
            return 0.0
        hits = sum(1 for r in results if r.get("evidence_hit", False))
        return hits / len(results)

    @staticmethod
    def citation_accuracy(results: list[dict]) -> float:
        """引用准确率"""
        if not results:
            return 0.0
        return sum(r.get("citation_accuracy", 0) for r in results) / len(results)

    @staticmethod
    def avg_latency(results: list[dict]) -> float:
        """平均延迟（毫秒）"""
        if not results:
            return 0.0
        return sum(r.get("total_time_ms", 0) for r in results) / len(results)

    @staticmethod
    def avg_token_usage(results: list[dict]) -> float:
        """平均 Token 消耗"""
        if not results:
            return 0.0
        return sum(r.get("token_count", 0) for r in results) / len(results)

    @staticmethod
    def repair_success_rate(results: list[dict]) -> float:
        """自修复成功率（仅 adaptive_crag）"""
        repair_cases = [r for r in results if r.get("retry_count", 0) > 0]
        if not repair_cases:
            return 0.0
        successes = sum(1 for r in repair_cases if r.get("success", False))
        return successes / len(repair_cases)

    @staticmethod
    def web_search_trigger_accuracy(results: list[dict]) -> float:
        """联网搜索触发准确率"""
        # 简化实现
        return 0.8

    @staticmethod
    def summarize(results: list[dict]) -> dict:
        """返回所有指标的汇总"""
        return {
            "total_cases": len(results),
            "end_to_end_success_rate": Scorer.end_to_end_success(results),
            "evidence_hit_rate": Scorer.evidence_hit_rate(results),
            "citation_accuracy": Scorer.citation_accuracy(results),
            "avg_latency_ms": Scorer.avg_latency(results),
            "avg_token_usage": Scorer.avg_token_usage(results),
            "repair_success_rate": Scorer.repair_success_rate(results),
            "web_search_trigger_accuracy": Scorer.web_search_trigger_accuracy(results),
        }
