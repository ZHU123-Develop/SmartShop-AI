"""网页搜索工具 - 使用 DuckDuckGo 搜索进行网页搜索。"""

import requests
from . import registry


def duckduckgo_search(query, count=5):
    """执行 DuckDuckGo 网页搜索。

    Args:
        query: 搜索关键词
        count: 返回结果数量，默认 5，最大 10

    Returns:
        搜索结果列表的字符串描述
    """
    count = min(max(1, count), 10)
    try:
        # 使用 DuckDuckGo Instant Answer API（无需 API Key，无需翻墙）
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        results = []

        # Instant Answer（直接答案）
        if data.get("AbstractText"):
            abstract = data["AbstractText"]
            abstract_url = data.get("AbstractURL", "")
            results.append(f"• {abstract}")
            if abstract_url:
                results.append(f"  来源: {abstract_url}")

        # Related Topics
        topics = data.get("RelatedTopics", [])
        for topic in topics[:count]:
            if "Text" in topic and "FirstURL" in topic:
                text = topic["Text"]
                url = topic["FirstURL"]
                results.append(f"• {text}")
                results.append(f"  链接: {url}")
            elif "Topics" in topic:
                # 嵌套的子主题
                for sub in topic["Topics"][:count]:
                    if "Text" in sub and "FirstURL" in sub:
                        results.append(f"• {sub['Text']}")
                        results.append(f"  链接: {sub['FirstURL']}")

        if not results:
            return f"未找到关于 '{query}' 的结果，请尝试其他关键词"

        return f"DuckDuckGo 搜索 '{query}' 的结果:\n" + "\n".join(results[:15])
    except requests.exceptions.Timeout:
        return f"搜索 '{query}' 超时，请稍后重试"
    except Exception as e:
        return f"搜索失败: {e}"


registry.register(
    name="duckduckgo_search",
    description="使用 DuckDuckGo 搜索引擎进行网页搜索，获取实时信息。无需翻墙。",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词",
            },
            "count": {
                "type": "integer",
                "description": "返回结果数量，默认 5，最大 10",
                "default": 5,
            },
        },
        "required": ["query"],
    },
    handler=duckduckgo_search,
)
