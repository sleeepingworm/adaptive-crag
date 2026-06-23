"""
联网搜索工具。使用 Tavily 或 Serper API。
"""

import os


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

    # 尝试使用 Tavily
    api_key = os.environ.get("CRAG_WEB_SEARCH_KEY") or os.environ.get("TAVILY_API_KEY")
    if api_key:
        return _search_tavily(query, max_results, api_key)

    # 尝试使用 Serper
    serper_key = os.environ.get("SERPER_API_KEY")
    if serper_key:
        return _search_serper(query, max_results, serper_key)

    return {
        "success": False,
        "result": None,
        "error": "未配置联网搜索 API Key（请设置 CRAG_WEB_SEARCH_KEY 或 TAVILY_API_KEY）",
    }


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
