"""Retrieve 节点：执行混合检索。"""

from .common import node_handler, get_current_retriever


@node_handler("retrieve", "正在检索文献...")
def retrieve_node(state: dict) -> dict:
    """执行混合检索"""
    retriever = get_current_retriever()
    if retriever is None:
        return {
            "retrieved_chunks": [],
            "errors": ["检索器未初始化"],
        }

    results = retriever.search(state.get("query", ""), top_k=10)
    return {"retrieved_chunks": results}