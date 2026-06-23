"""
安全边界与校验：静态检查代码安全性。
"""

import ast
import sys


def check_code_safety(
    code: str,
    restricted_modules: list[str] | None = None,
    allowed_packages: list[str] | None = None,
) -> tuple[bool, str]:
    """
    静态检查代码安全性。

    检查内容:
    1. import / from ... import 是否包含黑名单模块
    2. 是否包含 eval() / exec() / __import__() / compile()
    3. 是否包含 os.system / subprocess / open() 写系统路径

    返回:
        (True, "") 或 (False, "代码包含受限操作: ...")
    """
    restricted = restricted_modules or [
        "os", "subprocess", "sys", "shutil", "glob",
        "pathlib", "importlib", "ctypes", "socket", "requests",
        "multiprocessing", "threading", "signal",
    ]

    # 禁止的内置函数
    forbidden_calls = {"eval", "exec", "__import__", "compile", "open"}

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"代码语法错误: {e}"

    for node in ast.walk(tree):
        # 检查 import
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split(".")[0]
                if module_name in restricted:
                    return False, f"代码包含受限模块: {module_name}"

        # 检查 from ... import
        if isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split(".")[0]
                if module_name in restricted:
                    return False, f"代码包含受限模块: {module_name}"

        # 检查函数调用
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in forbidden_calls:
                    return False, f"代码包含禁止的操作: {node.func.id}()"
            elif isinstance(node.func, ast.Attribute):
                # 检查 os.system, os.popen 等
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id in ("os", "subprocess"):
                        return False, f"代码包含系统操作: {node.func.value.id}.{node.func.attr}()"

    return True, ""


def sanitize_imports(code: str, allowed: list[str]) -> str:
    """
    可选：将不在白名单的 import 注释掉，并添加注释提醒。
    MVP 阶段可直接拒绝，不修改。
    """
    return code
