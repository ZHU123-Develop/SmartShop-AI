"""网页搜索工具 - 使用 DuckDuckGo 进行网页搜索。"""

import requests
from . import registry


def web_search(query, count=5):
    """执行网页搜索。

    Args:
        query: 搜索关键词
        count: 返回结果数量，默认 5，最大 10

    Returns:
        搜索结果列表的字符串描述
    """
    count = min(max(1, count), 10)
    try:
        # 使用 DuckDuckGo Instant Answer API（免费，无需 Key）
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10,
            headers={"User-Agent": "DeepSeekChatBot/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()

        results = []

        # 摘要
        abstract = data.get("AbstractText", "")
        abstract_url = data.get("AbstractURL", "")
        if abstract:
            results.append(f"[摘要] {abstract}")
            if abstract_url:
                results.append(f"  来源: {abstract_url}")

        # 相关话题
        related = data.get("RelatedTopics", [])
        for topic in related[:count]:
            text = topic.get("Text", "")
            first_url = topic.get("FirstURL", "")
            if text:
                line = f"- {text}"
                if first_url:
                    line += f" ({first_url})"
                results.append(line)

        if not results:
            return f"未找到关于 '{query}' 的结果，请尝试其他关键词"

        return f"搜索 '{query}' 的结果:\n" + "\n".join(results[:count])
    except requests.exceptions.Timeout:
        return f"搜索 '{query}' 超时，请稍后重试"
    except Exception as e:
        return f"搜索失败: {e}"


register(
    name="web_search",
    description="使用 DuckDuckGo 搜索引擎进行网页搜索，获取实时信息。",
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
    handler=web_search,
)
