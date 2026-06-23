"""
GraphState 扩展和 schema 绑定。
"""

from adaptive_crag.schema import GraphState


def create_initial_state(query: str, uploaded_files: list[str] | None = None) -> dict:
    """
    根据用户输入创建初始 GraphState 的 dict 形态。

    Args:
        query: 用户问题
        uploaded_files: 上传文件路径列表

    Returns:
        GraphState 的 dict 形态
    """
    state = GraphState(
        query=query,
        uploaded_files=uploaded_files or [],
        current_step="init",
    )
    return _dataclass_to_dict(state)


def _dataclass_to_dict(obj) -> dict:
    """将 dataclass 递归转为 dict"""
    from dataclasses import asdict
    return asdict(obj)
