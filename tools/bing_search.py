"""网页搜索工具 - 使用 Bing 搜索进行网页搜索（国内可访问）。"""

import requests
from . import registry


def bing_search(query, count=5):
    """执行 Bing 网页搜索。

    Args:
        query: 搜索关键词
        count: 返回结果数量，默认 5，最大 10

    Returns:
        搜索结果列表的字符串描述
    """
    count = min(max(1, count), 10)
    try:
        # 使用 Bing 搜索结果页面抓取（无需 API Key）
        resp = requests.get(
            "https://www.bing.com/search",
            params={"q": query, "count": count},
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )
        resp.raise_for_status()

        # 简单的 HTML 解析（不使用 BeautifulSoup 依赖）
        import html
        from html.parser import HTMLParser

        results = _parse_bing_results(resp.text, count)

        if not results:
            return f"未找到关于 '{query}' 的结果，请尝试其他关键词"

        return f"搜索 '{query}' 的结果:\n" + "\n".join(results)
    except requests.exceptions.Timeout:
        return f"搜索 '{query}' 超时，请稍后重试"
    except Exception as e:
        return f"搜索失败: {e}"


def _parse_bing_results(html_text, max_results=5):
    """从 Bing 搜索结果页面提取标题、URL 和摘要。"""
    results = []

    # 使用简单的 HTML 解析器
    class BingParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.results = []
            self.in_result = False
            self.in_title = False
            self.in_url = False
            self.in_snippet = False
            self.current = {}
            self.text_buffer = ""
            self.tag_stack = []

        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            class_val = attrs_dict.get("class", "")

            if tag == "li" and "b_algo" in class_val:
                self.in_result = True
                self.current = {}
                self.text_buffer = ""
            elif tag == "h2" and self.in_result:
                self.in_title = True
                self.text_buffer = ""
            elif tag == "a" and self.in_title:
                url = attrs_dict.get("href", "")
                if url and url.startswith("https://"):
                    self.current["url"] = url
            elif tag == "cite" and self.in_result:
                self.in_url = True
                self.text_buffer = ""
            elif tag == "p" and self.in_result:
                self.in_snippet = True
                self.text_buffer = ""

        def handle_endtag(self, tag):
            if self.in_title and tag == "h2":
                self.in_title = False
                if self.text_buffer:
                    self.current["title"] = self.text_buffer.strip()
            elif self.in_url and tag == "cite":
                self.in_url = False
                if self.text_buffer:
                    self.current["domain"] = self.text_buffer.strip()
            elif self.in_snippet and tag == "p":
                self.in_snippet = False
                if self.text_buffer:
                    self.current["snippet"] = self.text_buffer.strip()
            elif tag == "li" and self.in_result:
                self.in_result = False
                if self.current.get("title"):
                    self.results.append(self.current)
                self.current = {}

        def handle_data(self, data):
            if self.in_title or self.in_url or self.in_snippet:
                self.text_buffer += data

    parser = BingParser()
    parser.feed(html_text)

    for item in parser.results[:max_results]:
        line = f"• {item.get('title', '')}"
        if item.get("snippet"):
            line += f"\n  {item.get('snippet', '')}"
        if item.get("url"):
            line += f"\n  链接: {item.get('url', '')}"
        results.append(line)

    return results


registry.register(
    name="web_search",
    description="使用 Bing 搜索引擎进行网页搜索，获取实时信息。",
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
    handler=bing_search,
)
