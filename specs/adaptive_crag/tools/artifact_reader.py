"""
产物读取工具。供 Report Agent 调用。
"""

import os
import base64


def artifact_reader(params: dict) -> dict:
    """
    产物读取工具。

    params:
        task_id: str
        artifact_type: str  # "chart" | "log" | "report" | "data"
        path: str
    """
    task_id = params.get("task_id", "")
    artifact_type = params.get("artifact_type", "")
    path = params.get("path", "")

    if not task_id or not artifact_type or not path:
        return {"success": False, "result": None, "error": "参数不完整"}

    if not os.path.exists(path):
        return {"success": False, "result": None, "error": f"文件不存在: {path}"}

    try:
        if artifact_type == "chart":
            # 图表：返回 base64
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            ext = path.split(".")[-1] if "." in path else "png"
            return {
                "success": True,
                "result": {
                    "type": "chart",
                    "content": f"data:image/{ext};base64,{data}",
                    "path": path,
                },
            }
        elif artifact_type in ("log", "report", "data"):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {
                "success": True,
                "result": {
                    "type": artifact_type,
                    "content": content[:5000],  # 截断长内容
                    "path": path,
                },
            }
        else:
            return {"success": False, "result": None, "error": f"不支持的产物类型: {artifact_type}"}

    except Exception as e:
        return {"success": False, "result": None, "error": f"读取产物失败: {str(e)}"}
