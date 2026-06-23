# 单元测试说明书：沙箱执行层 (sandbox)

## 对应模块
`06_sandbox.md`

## 目标测试文件
```
tests/
    test_sandbox/
        __init__.py
        conftest.py              # 临时目录、测试用数据文件
        test_runner.py           # SandboxRunner 执行测试
        test_security.py         # 安全检查测试
        test_error_parser.py     # 错误解析测试
```

## 运行方式
```bash
pytest tests/test_sandbox/ -v
```

## 测试策略
- 真的用 subprocess 执行简单脚本（print 1+1 级别的代码）
- 不要执行真正有副作用的代码
- security 测试既测白名单也测黑名单

## 测试用例清单

### test_runner.py

```python
@pytest.fixture
def runner(temp_dir):
    return SandboxRunner(timeout_seconds=10)

@pytest.fixture
def temp_dir(tmp_path):
    return str(tmp_path)

def test_execute_simple_print(runner, temp_dir):
    """print("hello") -> stdout="hello\n" success=True"""

def test_execute_pandas_code(runner, temp_dir, sample_csv_path):
    """使用 pandas 读取 CSV 并打印列名 -> stdout 包含列名"""

def test_execute_matplotlib(runner, temp_dir):
    """绘制简单图表并保存 -> generated_files 包含 .png"""

def test_execute_syntax_error(runner, temp_dir):
    """语法错误 -> success=False, stderr 包含 SyntaxError"""

def test_execute_runtime_error(runner, temp_dir):
    """运行时错误（除以零） -> success=False, traceback 不为 None"""

def test_execute_timeout(runner, temp_dir):
    """无限循环 -> 超时后返回 success=False, error 包含超时消息"""

def test_execute_no_output(runner, temp_dir):
    """无输出的代码 -> stdout 为空字符串"""

def test_execute_empty_code(runner, temp_dir):
    """空代码 -> success=True, stdout 为空"""

def test_execute_generated_files(runner, temp_dir):
    """生成多个图表的代码 -> generated_files 包含所有图表路径"""

def test_execute_with_data_files(runner, temp_dir, sample_csv_path):
    """传入 data_files 后代码能正确读取"""

def test_execute_stdout_truncated(runner, temp_dir):
    """超长 stdout 被截断到 max_output_chars"""

def test_runner_creates_temp_dir(runner, temp_dir):
    """代码在临时目录执行，不在当前目录留文件"""
```

### test_security.py

```python
def test_block_os_import():
    """import os -> check_code_safety 返回 False"""

def test_block_subprocess_import():
    """import subprocess -> False"""

def test_block_socket_import():
    """import socket -> False"""

def test_block_eval_usage():
    """eval("1+1") -> False"""

def test_block_exec_usage():
    """exec("x=1") -> False"""

def test_allow_pandas_import():
    """import pandas as pd -> True"""

def test_allow_numpy_import():
    """import numpy as np -> True"""

def test_allow_matplotlib_import():
    """import matplotlib.pyplot as plt -> True"""

def test_allow_standard_lib():
    """import json/csv/datetime/math/collections -> True"""

def test_block_os_system():
    """os.system("dir") 即使通过 from os import system -> False"""

def test_block_open_write_system_path():
    """open("C:/windows/system.ini", "w") -> False"""

def test_allow_open_read_data_file():
    """open("data.csv", "r") -> True（读取数据文件是允许的）"""

def test_security_empty_code():
    """空代码 -> True"""

def test_security_comment_only():
    """只有注释的代码 -> True"""
```

### test_error_parser.py

```python
def test_parse_name_error():
    """
    traceback = 'NameError: name "df" is not defined'
    -> ParsedError(error_type="NameError", line_number=?, likely_cause=?)
    """

def test_parse_type_error_missing_arg():
    """TypeError -> 正确解析"""

def test_parse_key_error():
    """KeyError: 'column_name' -> 正确解析"""

def test_parse_value_error():
    """ValueError -> 正确解析"""

def test_parse_module_not_found():
    """ModuleNotFoundError -> 正确解析"""

def test_parse_empty_traceback():
    """空 traceback -> None"""

def test_parse_garbled_traceback():
    """乱码 traceback -> 返回 None 不崩溃"""

def test_summarize_error_basic(fake_artifact):
    """summarize_error 返回 1-3 句中文字符串"""

def test_summarize_error_success_artifact(fake_success_artifact):
    """成功的 artifact 返回 "执行成功""""
```