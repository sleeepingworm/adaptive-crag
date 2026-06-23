"""
adaptive_crag.evaluation - Benchmark 评测层
===========================================
管理黄金测试集、跑分引擎、评分器和对照实验。
"""

from .test_suite import TestSuite
from .runner import BenchmarkRunner
from .scorers import Scorer
from .comparators import Comparator
from .sample_questions import get_sample_questions

__all__ = [
    "TestSuite",
    "BenchmarkRunner",
    "Scorer",
    "Comparator",
    "get_sample_questions",
]
