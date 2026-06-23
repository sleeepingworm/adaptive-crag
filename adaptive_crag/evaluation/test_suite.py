"""
黄金测试集管理器。从 JSON/CSV 文件加载测试样例。
"""

import json
import os
from adaptive_crag.schema import BenchmarkCase


class TestSuite:
    """
    黄金测试集管理器。
    """

    def __init__(self, data_path: str):
        self.data_path = data_path
        self._cases: list[BenchmarkCase] = []

    def load_all(self) -> list[BenchmarkCase]:
        """加载全部测试题"""
        if not os.path.exists(self.data_path):
            # 使用内置样例
            from .sample_questions import get_sample_questions
            self._cases = get_sample_questions()
        else:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._cases = [BenchmarkCase(**item) for item in data]

        return self._cases

    def filter_by_category(self, category: str) -> list[BenchmarkCase]:
        """按类别筛选"""
        if not self._cases:
            self.load_all()
        return [c for c in self._cases if c.category == category]

    def get_stats(self) -> dict:
        """返回测试集统计信息"""
        if not self._cases:
            self.load_all()

        categories = {}
        for c in self._cases:
            categories[c.category] = categories.get(c.category, 0) + 1

        return {
            "total": len(self._cases),
            "categories": categories,
        }
