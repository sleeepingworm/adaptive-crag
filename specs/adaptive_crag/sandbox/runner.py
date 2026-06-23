"""
子进程执行器：在隔离子进程中执行 Python 代码，
捕获 stdout、stderr、traceback，收集产物。
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil

from adaptive_crag.schema import ExecutionArtifact
from adaptive_crag.config.settings import SandboxConfig
from .security import check_code_safety


class SandboxRunner:
    """
    在隔离子进程中执行 Python 代码。

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
        max_output_chars: int = 10000,
    ):
        self.allowed_packages = allowed_packages or SandboxConfig().allowed_packages
        self.restricted_modules = restricted_modules or SandboxConfig().restricted_modules
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars

    def execute(
        self,
        code: str,
        data_files: list[str] | None = None,
        output_dir: str | None = None,
        timeout: int | None = None,
    ) -> ExecutionArtifact:
        """核心执行方法"""
        # 安全检查
        is_safe, reason = check_code_safety(code, self.restricted_modules, self.allowed_packages)
        if not is_safe:
            return ExecutionArtifact(
                success=False,
                stderr=f"代码安全校验失败: {reason}",
                exit_code=-1,
            )

        timeout = timeout or self.timeout_seconds
        data_files = data_files or []
        output_dir = output_dir or tempfile.mkdtemp()
        os.makedirs(output_dir, exist_ok=True)

        # 创建临时工作目录
        work_dir = tempfile.mkdtemp(prefix="crag_sandbox_")

        try:
            # 复制数据文件到工作目录
            for f in data_files:
                if os.path.exists(f):
                    shutil.copy2(f, work_dir)

            # 写入脚本
            script_path = os.path.join(work_dir, "script.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 设置环境变量：限制文件访问
            env = os.environ.copy()
            env["CRAG_OUTPUT_DIR"] = output_dir
            env["CRAG_WORK_DIR"] = work_dir

            # 执行
            start_time = time.time()
            try:
                result = subprocess.run(
                    [sys.executable, script_path],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                )
                elapsed_ms = int((time.time() - start_time) * 1000)

                stdout = result.stdout[:self.max_output_chars] if result.stdout else ""
                stderr = result.stderr[:self.max_output_chars] if result.stderr else ""

                artifact = ExecutionArtifact(
                    success=result.returncode == 0,
                    stdout=stdout,
                    stderr=stderr,
                    traceback=stderr if result.returncode != 0 else None,
                    execution_time_ms=elapsed_ms,
                    exit_code=result.returncode,
                )

            except subprocess.TimeoutExpired:
                elapsed_ms = int((time.time() - start_time) * 1000)
                artifact = ExecutionArtifact(
                    success=False,
                    stderr=f"执行超时（{timeout}秒）",
                    traceback=f"TimeoutError: 代码执行超过 {timeout} 秒限制",
                    execution_time_ms=elapsed_ms,
                    exit_code=-1,
                )

            # 收集生成文件
            artifact.generated_files = self._collect_generated_files(output_dir)
            artifact.data_files = self._collect_data_files(output_dir)

            return artifact

        finally:
            # 清理临时目录
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass

    def _collect_generated_files(self, output_dir: str) -> list[str]:
        """扫描 output_dir，返回生成的 .png/.csv/.json 等文件列表"""
        generated = []
        if not os.path.exists(output_dir):
            return generated
        for fname in os.listdir(output_dir):
            ext = fname.lower().split(".")[-1] if "." in fname else ""
            if ext in ("png", "jpg", "jpeg", "svg", "pdf", "csv", "json", "xlsx"):
                fpath = os.path.join(output_dir, fname)
                if os.path.isfile(fpath):
                    generated.append(fpath)
        return generated

    def _collect_data_files(self, output_dir: str) -> list[str]:
        """收集生成的数据文件"""
        return self._collect_generated_files(output_dir)


def create_runner(config: SandboxConfig | None = None) -> SandboxRunner:
    """工厂函数，从配置创建 SandboxRunner 实例"""
    if config is None:
        config = SandboxConfig()
    return SandboxRunner(
        allowed_packages=config.allowed_packages,
        restricted_modules=config.restricted_modules,
        timeout_seconds=config.timeout_seconds,
        max_output_chars=config.max_output_chars,
    )


def execute_safely(code: str, data_files: list[str], output_dir: str,
                   config: SandboxConfig | None = None) -> ExecutionArtifact:
    """便捷函数：直接执行代码"""
    runner = create_runner(config)
    return runner.execute(code, data_files, output_dir)
