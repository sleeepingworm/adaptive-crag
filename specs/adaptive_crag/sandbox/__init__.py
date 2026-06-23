"""
adaptive_crag.sandbox - 沙箱执行层
=================================
在隔离子进程中执行 Python 代码，带安全限制、超时控制和错误解析。
"""

from .runner import SandboxRunner, execute_safely, create_runner
from .security import check_code_safety
from .error_parser import parse_traceback, summarize_error, ParsedError

__all__ = [
    "SandboxRunner",
    "execute_safely",
    "create_runner",
    "check_code_safety",
    "parse_traceback",
    "summarize_error",
    "ParsedError",
]
