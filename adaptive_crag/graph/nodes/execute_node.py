"""Execute 节点：调用沙箱执行器执行代码。"""

import os
import tempfile

from .common import node_handler
from adaptive_crag.sandbox import create_runner


@node_handler("execute", "正在执行分析代码...")
def execute_node(state: dict) -> dict:
    """执行生成的代码"""
    code = state.get("code", "")
    if not code or code == "# 无需数据分析\nprint('分析完成，无需额外代码执行')":
        return {
            "execution_result": {
                "success": True,
                "stdout": "无需代码执行",
                "stderr": "",
                "traceback": None,
                "generated_files": [],
                "data_files": [],
                "execution_time_ms": 0,
                "exit_code": 0,
            },
        }

    data_files = state.get("uploaded_files", [])
    output_dir = tempfile.mkdtemp(prefix="crag_exec_")

    try:
        runner = create_runner()
        artifact = runner.execute(code=code, data_files=data_files, output_dir=output_dir)
        return {
            "execution_result": artifact.to_dict(),
            "execution_error": artifact.stderr if not artifact.success else None,
        }
    except Exception as e:
        return {
            "execution_result": {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "traceback": str(e),
                "generated_files": [],
                "data_files": [],
                "execution_time_ms": 0,
                "exit_code": -1,
            },
            "execution_error": str(e),
            "errors": [f"代码执行失败: {str(e)}"],
        }