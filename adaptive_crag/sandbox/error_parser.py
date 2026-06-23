"""
错误信息解析：提取结构化错误信息供 Self-Correction 模块使用。
"""

import re
import traceback as tb_module
from dataclasses import dataclass, field


@dataclass
class ParsedError:
    """结构化错误信息"""
    error_type: str = ""
    error_message: str = ""
    line_number: int | None = None
    relevant_line: str | None = None
    likely_cause: str = ""


def parse_traceback(traceback_text: str, code: str | None = None) -> ParsedError | None:
    """
    解析 traceback 文本，提取结构化错误信息。

    常见错误类型:
    - NameError: 变量未定义
    - KeyError: 字典键不存在 / DataFrame 列不存在
    - TypeError: 类型不匹配
    - ValueError: 值不合法
    - ModuleNotFoundError: 模块未安装
    - FileNotFoundError: 文件不存在
    - AttributeError: 对象没有某属性
    - IndexError: 索引越界
    - ZeroDivisionError: 除零
    """
    if not traceback_text:
        return None

    # 提取错误类型和消息
    error_match = re.search(
        r"(Traceback.*\n)?.*?(\w+(?:Error|Warning|Exception)):\s*(.*?)(?:\n|$)",
        traceback_text,
        re.DOTALL,
    )

    if not error_match:
        return None

    error_type = error_match.group(2)
    error_message = error_match.group(3).strip()

    # 提取行号
    line_match = re.search(r"line\s+(\d+)", traceback_text)
    line_number = int(line_match.group(1)) if line_match else None

    # 提取相关代码行
    relevant_line = None
    if line_number and code:
        lines = code.split("\n")
        if 1 <= line_number <= len(lines):
            relevant_line = lines[line_number - 1].strip()

    # 推断原因
    likely_cause = _infer_cause(error_type, error_message, relevant_line)

    return ParsedError(
        error_type=error_type,
        error_message=error_message,
        line_number=line_number,
        relevant_line=relevant_line,
        likely_cause=likely_cause,
    )


def _infer_cause(error_type: str, error_message: str, relevant_line: str | None) -> str:
    """推断错误的中文原因"""
    cause_map = {
        "NameError": "变量未定义，请检查变量名拼写或确保变量已赋值",
        "KeyError": "键或列名不存在，请检查字典键名或 DataFrame 列名",
        "TypeError": "类型不匹配，请检查操作数的数据类型",
        "ValueError": "值不合法，请检查输入值的范围和格式",
        "ModuleNotFoundError": "缺少依赖模块，请安装所需 Python 包",
        "FileNotFoundError": "文件不存在，请检查文件路径",
        "AttributeError": "对象没有该属性，请检查对象类型和方法名",
        "IndexError": "索引越界，请检查列表长度和索引范围",
        "ZeroDivisionError": "除零错误，请检查除数是否为零",
        "ImportError": "导入失败，请检查模块名或安装依赖",
        "IndentationError": "缩进错误，请检查代码缩进格式",
        "SyntaxError": "语法错误，请检查代码语法",
    }

    cause = cause_map.get(error_type, f"发生了 {error_type} 错误")

    # 细化常见错误
    if error_type == "NameError":
        var_match = re.search(r"name\s+'(\w+)'", error_message)
        if var_match:
            cause = f"变量 '{var_match.group(1)}' 未定义。请检查变量名拼写是否正确，或确保在使用前已赋值。"

    elif error_type == "KeyError":
        key_match = re.search(r"'([^']*)'", error_message)
        if key_match:
            cause = f"键/列 '{key_match.group(1)}' 不存在。请检查列名是否正确，或使用 df.columns 查看所有列。"

    elif error_type == "AttributeError":
        obj_match = re.search(r"'(\w+)' object has no attribute '(\w+)'", error_message)
        if obj_match:
            cause = f"{obj_match.group(1)} 对象没有 '{obj_match.group(2)}' 属性。请检查对象类型是否正确。"

    return cause


def summarize_error(artifact) -> str:
    """
    将 ExecutionArtifact 的错误信息简化为 2-3 句摘要，
    供 LLM 快速理解错误原因。
    """
    text = artifact.stderr or artifact.traceback or ""
    if not text:
        return "未知错误"

    parsed = parse_traceback(text)
    if parsed:
        summary = f"{parsed.error_type}: {parsed.error_message}"
        if parsed.likely_cause:
            summary += f"。{parsed.likely_cause}"
        if parsed.line_number:
            summary += f"（第 {parsed.line_number} 行）"
        return summary

    # fallback
    return text[:200]
