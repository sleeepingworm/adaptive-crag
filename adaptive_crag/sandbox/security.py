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
        "subprocess", "shutil", "glob",
        "importlib", "ctypes", "socket", "requests",
        "multiprocessing", "threading", "signal",
    ]

    # 禁止的内置函数
    forbidden_calls = {"eval", "exec", "__import__", "compile", "open"}
    # os 模块中危险的系统调用（允许 os.path、os.listdir 等安全操作）
    dangerous_os_calls = {
        "system", "popen", "popen2", "popen3", "popen4",
        "execl", "execle", "execlp", "execlpe",
        "execv", "execve", "execvp", "execvpe",
        "spawnl", "spawnle", "spawnlp", "spawnlpe",
        "spawnv", "spawnve", "spawnvp", "spawnvpe",
        "fork", "forkpty", "kill",
    }

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

        # 检查危险的系统调用（subprocess 全部禁止，os 只禁止危险方法）
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in forbidden_calls:
                    return False, f"代码包含禁止的操作: {node.func.id}()"
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "subprocess":
                        return False, f"代码包含系统操作: subprocess.{node.func.attr}()"
                    if node.func.value.id == "os" and node.func.attr in dangerous_os_calls:
                        return False, f"代码包含系统操作: os.{node.func.attr}()"

    return True, ""


def sanitize_imports(code: str, allowed: list[str]) -> str:
    """将不在白名单的 import 语句注释掉。

    AST 解析代码 → 找出所有 import / from import → 检查顶层模块名
    是否在 allowed 中 → 不在则注释掉对应行。

    白名单模式与黑名单模式互斥：白名单模式下只允许 stdlib + 指定第三方包，
    其余 import 一律移除。当前 SandboxRunner 默认使用黑名单（check_code_safety），
    此函数供未来切到白名单模式时使用。
    """
    if not allowed:
        return code

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    lines_to_comment: set[int] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_module = alias.name.split(".")[0]
                if top_module not in allowed:
                    start = node.lineno
                    end = node.end_lineno or node.lineno
                    for i in range(start, end + 1):
                        lines_to_comment.add(i)
                    break

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_module = node.module.split(".")[0]
                if top_module not in allowed:
                    start = node.lineno
                    end = node.end_lineno or node.lineno
                    for i in range(start, end + 1):
                        lines_to_comment.add(i)

    if not lines_to_comment:
        return code

    lines = code.split("\n")
    for line_no in sorted(lines_to_comment, reverse=True):
        idx = line_no - 1
        if idx < len(lines) and not lines[idx].startswith("#"):
            lines[idx] = f"# [sanitized] {lines[idx]}"

    return "\n".join(lines)
