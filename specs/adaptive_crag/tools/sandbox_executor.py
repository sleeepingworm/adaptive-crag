"""
代码沙箱执行工具。
"""

import tempfile
from adaptive_crag.sandbox import create_runner


def sandbox_executor(params: dict) -> dict:
    """
    代码沙箱执行工具。

    params:
        code: str
        data_files: list[str] = []
        output_dir: str = None
        timeout: int = 60
    """
    code = params.get("code", "")
    data_files = params.get("data_files", [])
    output_dir = params.get("output_dir", tempfile.mkdtemp(prefix="crag_exec_"))
    timeout = params.get("timeout", 60)

    if not code:
        return {"success": False, "result": None, "error": "code 不能为空"}

    try:
        runner = create_runner()
        artifact = runner.execute(
            code=code,
            data_files=data_files,
            output_dir=output_dir,
            timeout=timeout,
        )

        return {
            "success": artifact.success,
            "result": artifact.to_dict(),
            "error": artifact.stderr if not artifact.success else None,
        }
    except Exception as e:
        return {"success": False, "result": None, "error": f"沙箱执行失败: {str(e)}"}
