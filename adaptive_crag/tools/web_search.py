"""
联网搜索工具。支持 DashScope(百炼)、Tavily、Serper。
"""

import os
import json


def _get_dashscope_api_key() -> str | None:
    """从百炼 CLI 配置中读取 DashScope API Key"""
    config_path = os.path.expanduser("~/.bailian/config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                cfg = json.load(f)
                return cfg.get("api_key")
        except Exception:
            pass
    return os.environ.get("DASHSCOPE_API_KEY")


def web_search(params: dict) -> dict:
    """
    联网搜索补偿工具。

    params:
        query: str
        max_results: int = 5
    """
    query = params.get("query", "")
    max_results = params.get("max_results", 5)

    if not query:
        return {"success": False, "result": None, "error": "query 不能为空"}

    # 1. 尝试 DashScope（百炼）搜索
    dashscope_key = _get_dashscope_api_key()
    if dashscope_key:
        return _search_dashscope(query, max_results, dashscope_key)

    # 2. 尝试 Tavily
    api_key = os.environ.get("CRAG_WEB_SEARCH_KEY") or os.environ.get("TAVILY_API_KEY")
    if api_key:
        return _search_tavily(query, max_results, api_key)

    # 3. 尝试 Serper
    serper_key = os.environ.get("SERPER_API_KEY")
    if serper_key:
        return _search_serper(query, max_results, serper_key)

    return {
        "success": False,
        "result": None,
        "error": "未配置联网搜索 API Key（请设置 TAVILY_API_KEY、SERPER_API_KEY，或使用 bl auth login 配置百炼）",
    }


def _search_dashscope(query: str, max_results: int, api_key: str) -> dict:
    """使用 DashScope（百炼）搜索，通过 qwen-turbo + enable_search 获取搜索结果"""
    import requests

    try:
        resp = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "qwen-turbo",
                "messages": [{"role": "user", "content": f"search: {query}"}],
                "enable_search": True,
            },
            timeout=30,
        )
        data = resp.json()

        if resp.status_code != 200:
            return {
                "success": False,
                "result": None,
                "error": f"DashScope 搜索失败: {data.get('message', str(resp.status_code))}",
            }

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        results = [{
            "title": f"搜索: {query}",
            "url": "",
            "snippet": content[:300],
            "content": content,
        }]

        return {
            "success": True,
            "result": {
                "query": query,
                "results": results,
                "source": "dashscope",
            },
        }
    except Exception as e:
        return {"success": False, "result": None, "error": f"DashScope 搜索失败: {str(e)}"}


def _search_tavily(query: str, max_results: int, api_key: str) -> dict:
    """使用 Tavily API 搜索"""
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=max_results)
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", ""),
                "content": r.get("content", ""),
            }
            for r in response.get("results", [])
        ]
        return {
            "success": True,
            "result": {
                "query": query,
                "results": results,
                "source": "tavily",
            },
        }
    except Exception as e:
        return {"success": False, "result": None, "error": f"联网搜索失败: {str(e)}"}


def _search_serper(query: str, max_results: int, api_key: str) -> dict:
    """使用 Serper API 搜索"""
    import requests
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": max_results},
            headers={"X-API-KEY": api_key},
            timeout=10,
        )
        data = response.json()
        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
                "content": r.get("snippet", ""),
            }
            for r in data.get("organic", [])
        ]
        return {
            "success": True,
            "result": {
                "query": query,
                "results": results,
                "source": "serper",
            },
        }
    except Exception as e:
        return {"success": False, "result": None, "error": f"联网搜索失败: {str(e)}"}