# 模块说明书：沙箱执行层 (sandbox)

## 所属层级
能力工具层

## 目标目录
`adaptive_crag/sandbox/`

生成文件：
```
adaptive_crag/sandbox/
    __init__.py             # 导出 SandboxRunner
    runner.py               # 子进程执行器
    security.py             # 安全边界与校验
    error_parser.py         # 错误信息解析
```

## 依赖模块

- **必须先生成**：`01_schema`（使用 ExecutionArtifact）

## 职责边界

**做：**
- 接收 Python 代码文本，在隔离子进程中执行
- 限制进程的目录访问权限
- 设置执行超时
- 捕获 stdout、stderr、traceback
- 收集生成的图表文件和数据文件
- 校验代码是否包含黑名单模块

**不做：**
- 不决定执行什么代码（上游 Agent 决定）
- 不修改代码
- 不联网
- 不做 Docker 容器化（MVP 用 subprocess 即可）

## 核心接口

### runner.py

```python
import subprocess
import tempfile
import os
import time

class SandboxRunner:
    """
    在隔离子进程中执行 Python 代码。

    执行流程:
    1. 校验代码安全（security.check_code_safety）
    2. 将代码写入临时 .py 文件
    3. 将数据文件复制到受控工作目录
    4. 启动 subprocess 执行
    5. 捕获输出和产物
    6. 清理临时文件

    安全约束:
    - 只允许读取指定的 data_files
    - 只允许写入指定的 output_dir
    - 运行超时由 timeout_seconds 控制
    """

    def __init__(
        self,
        allowed_packages: list[str] | None = None,
        restricted_modules: list[str] | None = None,
        timeout_seconds: int = 60,
        max_output_chars: int = 10000
    ):
        ...

    def execute(
        self,
        code: str,
        data_files: list[str] | None = None,
        output_dir: str | None = None,
        timeout: int | None = None
    ) -> ExecutionArtifact:
        """
        核心执行方法。

        步骤:
        1. 调用 security.check_code_safety(code) 校验
        2. 创建临时工作目录
        3. 将 data_files 复制到工作目录
        4. 将 code 写入 work_dir/script.py
        5. subprocess.run(
            [sys.executable, "script.py"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
           )
        6. 收集 output_dir 下的生成文件
        7. 构造 ExecutionArtifact 返回

        如果 security.check 失败:
            返回 ExecutionArtifact(success=False, stderr="代码包含受限模块: os")
        """

    def _collect_generated_files(self, output_dir: str) -> list[str]:
        """
        扫描 output_dir，返回生成的 .png/.csv/.json 文件列表。
        排除 .py 文件。
        """
```

### security.py

```python
def check_code_safety(
    code: str,
    restricted_modules: list[str] | None = None,
    allowed_packages: list[str] | None = None
) -> tuple[bool, str]:
    """
    静态检查代码安全性。

    检查内容:
    1. import / from ... import 是否包含黑名单模块
    2. 是否包含 eval() / exec() / __import__() / compile()
    3. 是否包含 os.system / subprocess / open() 写系统路径
    4. 是否包含疑似删除文件的命令

    返回:
        (True, "") 或 (False, "代码包含受限操作: os")
    """

def sanitize_imports(code: str, allowed: list[str]) -> str:
    """
    可选：将不在白名单的 import 注释掉，并添加注释提醒。
    MVP 阶段可直接拒绝，不修改。
    """
```

### error_parser.py

```python
@dataclass
class ParsedError:
    error_type: str          # NameError, TypeError, ValueError, ModuleNotFoundError...
    error_message: str       # name 'xxx' is not defined
    line_number: int | None  # 出错行号
    relevant_line: str | None  # 出错行的代码
    likely_cause: str        # 简化的中文原因描述

def parse_traceback(traceback_text: str, code: str | None = None) -> ParsedError | None:
    """
    解析 traceback 文本，提取结构化错误信息。
    用于 Self-Correction 模块理解错误原因。

    如果无法解析返回 None。
    """

def summarize_error(artifact: ExecutionArtifact) -> str:
    """
    将 ExecutionArtifact 的错误信息简化为 2-3 句摘要，
    供 LLM 快速理解错误原因。

    示例输出:
    "NameError: 'df' 未定义。第 12 行使用了未创建的变量 df。
     可能是 DataFrame 变量名拼写错误，或前一步未正确赋值。"
    """
```

### __init__.py

```python
def create_runner(config: SandboxConfig) -> SandboxRunner:
    """
    工厂函数，从配置创建 SandboxRunner 实例。
    """

def execute_safely(code: str, data_files: list[str], output_dir: str, config: SandboxConfig | None = None) -> ExecutionArtifact:
    """
    便捷函数：直接执行代码。
    内部创建 SandboxRunner 并调用 execute。
    """
```

## 代码执行的具体流程

```
用户代码 -> check_code_safety -> 拒绝 (返回错误)
                               -> 通过
                                  -> 写入临时文件
                                  -> subprocess.run(python script.py)
                                     -> 正常完成: 收集 stdout + 生成文件
                                     -> 超时: timeout 错误
                                     -> 异常退出: 收集 stderr + traceback
                                  -> 清理临时目录
                                  -> 返回 ExecutionArtifact
```

## 实现约束

1. **依赖限制**：禁止 `os`、`subprocess`、`sys`、`shutil`、`requests`、`socket` 等系统/网络模块
2. **白名单机制**：默认允许 `pandas`、`numpy`、`matplotlib`、`seaborn`、`scipy`、`statsmodels`、`sklearn`
3. **文件访问**：代码只能读写 `data_files` 和 `output_dir` 所在目录，不能访问上层路径
4. **超时处理**：使用 `subprocess.run(timeout=...)` 而非信号机制
5. **路径转义**：所有用户代码中引用的文件路径应转为受控目录内的相对路径
6. **临时文件清理**：每次执行后清理临时目录，除非 debug 模式
7. **编码问题**：stdout/stderr 使用 UTF-8 解码，遇到错误用 `errors="replace"`

## 与上下游模块的对接

- **上游调用方**：LangGraph 的 sandbox_executor 工具节点
- **上游调用方**：Self-Correction 循环（根据 error 决定是否重试）
- **下游消费方**：error_parser 结果给 Repair Agent
- **数据流向**：`Code Agent -> tools/sandbox_executor -> SandboxRunner.execute() -> ExecutionArtifact`

## 测试要点

- 简单脚本（print 1+1）能正确返回 stdout
- 超出白名单的 import 被拒绝
- 执行超时时返回超时错误
- 生成 matplotlib 图表能在产物列表中找到
- 无错误脚本返回 success=True
- 错误脚本能在 ExecutionArtifact.traceback 中找到原因