"""
代码执行相关数据结构：ExecutionArtifact
"""

from dataclasses import dataclass, field


@dataclass
class ExecutionArtifact:
    """代码执行产物"""
    success: bool = False
    stdout: str = ""
    stderr: str = ""
    traceback: str | None = None
    generated_files: list[str] = field(default_factory=list)
    data_files: list[str] = field(default_factory=list)
    execution_time_ms: int = 0
    exit_code: int = -1

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "traceback": self.traceback,
            "generated_files": self.generated_files,
            "data_files": self.data_files,
            "execution_time_ms": self.execution_time_ms,
            "exit_code": self.exit_code,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ExecutionArtifact":
        return cls(
            success=d.get("success", False),
            stdout=d.get("stdout", ""),
            stderr=d.get("stderr", ""),
            traceback=d.get("traceback"),
            generated_files=d.get("generated_files", []),
            data_files=d.get("data_files", []),
            execution_time_ms=d.get("execution_time_ms", 0),
            exit_code=d.get("exit_code", -1),
        )
