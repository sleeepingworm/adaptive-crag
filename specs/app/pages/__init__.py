"""
页面模块初始化。
"""

from .upload_page import render_upload_page
from .task_page import render_task_page
from .report_page import render_report_page
from .benchmark_page import render_benchmark_page

__all__ = [
    "render_upload_page",
    "render_task_page",
    "render_report_page",
    "render_benchmark_page",
]
