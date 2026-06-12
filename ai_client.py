"""AI API 客户端 - 封装对话和工具调用逻辑。

支持通过 settings.json 或环境变量动态配置 API，集成 RAG 知识库检索。
"""

import json
import os
from openai import OpenAI
from tools.registry import get_all_tools, execute_tool

# ── RAG 知识库（延迟导入，避免循环依赖）─────────────────────────

_vector_store = None


def _get_vector_store():
    """延迟获取向量存储实例。"""
    global _vector_store
    if _vector_store is None:
        from rag.vector_store import VectorStore
        _vector_store = VectorStore()
    return _vector_store


def _set_vector_store(store):
    """由 app.py 注入共享的 VectorStore 实例，避免多连接问题。"""
    global _vector_store
    _vector_store = store


def _retrieve_context(message, top_k=3, similarity_threshold=0.5):
    """从知识库检索相关上下文。

    Args:
        message: 用户消息
        top_k: 返回片段数量
        similarity_threshold: 最低相似度阈值

    Returns:
        str: 格式化的上下文文本，无结果时返回空字符串
    """
    try:
        store = _get_vector_store()
        if store.count() == 0:
            return ""

        results = store.query(message, top_k=top_k, similarity_threshold=similarity_threshold)
        if not results:
            return ""

        # 格式化为引用文本
        context_parts = []
        for r in results:
            part = (
                f"【来源: {r.get('filename', r.get('source', '未知'))} "
                f"| 相关度: {r['score']}]\n{r['chunk']}"
            )
            context_parts.append(part)

        return "\n\n---\n\n".join(context_parts)
    except Exception:
        # 知识库不可用时静默降级
        return ""


# ── 配置 ──────────────────────────────────────────────────────────

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULT_API_KEY = ""
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"


def _load_settings():
    """从配置文件加载设置。"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_config():
    """获取当前 API 配置，优先级：环境变量 > settings.json > 默认值。"""
    settings = _load_settings()
    api_key = os.environ.get("LLM_API_KEY") or settings.get("api_key") or DEFAULT_API_KEY
    base_url = os.environ.get("LLM_BASE_URL") or settings.get("base_url") or DEFAULT_BASE_URL
    model = os.environ.get("LLM_MODEL") or settings.get("model") or DEFAULT_MODEL
    search_provider = settings.get("search_provider", "bing")
    return api_key, base_url, model, search_provider


def create_client():
    """根据当前配置创建 OpenAI 客户端。"""
    api_key, base_url, _, _ = get_config()
    if not api_key:
        raise RuntimeError("未配置 API Key，请在设置中填写")
    return OpenAI(api_key=api_key, base_url=base_url)


# ── 系统提示词 ────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = (
    "你是\"{shop_name}\"的AI智能客服助手，名叫\"小智\"。\n\n"
    "## 你的角色\n"
    "- 你是{shop_name}的专属客服，负责解答顾客的购物咨询、订单查询、退换货、物流追踪等问题\n"
    "- 语气亲切、专业、耐心，使用\"您\"称呼客户\n"
    "- 回答要简洁准确，避免冗长\n\n"
    "## 行为规则\n"
    "1. 当用户询问订单状态时，使用 query_order 工具查询\n"
    "2. 当用户追踪物流时，使用 query_logistics 工具查询\n"
    "3. 当用户咨询退换货时，使用 query_return_refund 工具查询\n"
    "4. 当用户查询会员信息时，使用 query_member_info 工具查询\n"
    "5. 当用户询问平台政策（如退换货规则、配送时效等）时，优先参考知识库内容回答\n"
    "6. 如果知识库和工具都无法提供答案，基于你的常识给出合理建议，并建议用户转接人工客服\n"
    "7. 不要编造订单号、物流信息或会员数据\n"
    "8. 所有回复使用中文\n\n"
    "## 回复风格\n"
    "- 开头可适当问候（如\"您好！\"、\"亲，\"）\n"
    "- 关键信息使用列表或表格格式，便于阅读\n"
    "- 结束时可提供进一步帮助（如\"还有其他问题吗？\"）\n\n"
    "## 营业时间\n"
    "本店营业时间为 {business_hours}，非营业时间可留言，我们将在上班后第一时间为您处理。"
)


def _build_system_prompt(context=""):
    """根据设置构建系统提示词，可选注入 RAG 上下文。"""
    settings = _load_settings()
    shop_name = settings.get("customer_service_name", "SmartShop")
    business_hours = settings.get("business_hours", "9:00-21:00")

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        shop_name=shop_name,
        business_hours=business_hours,
    )

    if context:
        system_prompt += (
            "\n\n=== 知识库参考资料 ===\n"
            f"{context}\n"
            "=== 参考资料结束 ===\n\n"
            "请优先基于以上知识库资料回答用户问题。如果知识库中没有相关信息，再根据你的知识回答。"
        )

    return system_prompt


# 默认系统提示词（用于模块级引用）
SYSTEM_PROMPT = _build_system_prompt()


def _filter_tools(search_provider):
    """返回所有工具列表。电商客服场景不需要按搜索 provider 过滤。"""
    return get_all_tools()


# ── 工具调用 ──────────────────────────────────────────────────────

def _handle_tool_calls(messages, client, model, search_provider="bing"):
    """处理工具调用循环。非流式，最多 5 轮。

    Args:
        messages: 对话消息列表（会被修改）
        client: OpenAI 客户端实例
        model: 模型名称
        search_provider: 搜索提供商 ("bing" 或 "duckduckgo")

    Returns:
        str: AI 的最终回复内容，或错误信息
    """
    tools = _filter_tools(search_provider)

    for _ in range(5):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        choice = response.choices[0]
        message_obj = choice.message

        if not message_obj.tool_calls:
            return message_obj.content or ""

        # 有工具调用，执行工具并追加到消息历史
        for tool_call in message_obj.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}

            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call],
            })

            result = execute_tool(func_name, **func_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "抱歉，我遇到了一些问题，请稍后重试。"


def _supports_tool_calling(model):
    """判断模型是否支持工具调用。

    根据已知信息判断，未知模型默认认为支持。
    """
    no_tools = [
        "glm-4-flash", "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k",
        "qwen-long", "glm-4-air", "glm-4-airx",
    ]
    return model not in no_tools


# ── 主对话接口 ────────────────────────────────────────────────────

def chat_stream(message, history=None):
    """流式对话接口。

    流程：
    1. 从知识库检索相关上下文（RAG）
    2. 构建系统提示词（客服角色 + RAG 上下文）
    3. 如果模型支持工具调用，在非流式模式下处理工具调用循环
    4. 工具调用完成后，将最终回复流式 yield 给调用者

    Args:
        message: 用户最新消息
        history: 历史对话列表 [{"role": "user/assistant", "content": "..."}]

    Yields:
        str: AI 回复的增量文本
    """
    if history is None:
        history = []

    api_key, base_url, model, search_provider = get_config()
    client = create_client()

    # 自动检索知识库上下文
    context = _retrieve_context(message)

    # 构建系统提示词（动态读取设置 + 注入 RAG 上下文）
    system_prompt = _build_system_prompt(context)

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": message},
    ]

    # 第一阶段：处理工具调用（如果模型支持）
    tool_result = None
    if _supports_tool_calling(model):
        try:
            tool_result = _handle_tool_calls(messages, client, model, search_provider)
            # 工具调用成功且有内容，直接返回结果（分块 yield 模拟流式效果）
            if tool_result:
                chunk_size = 10
                for i in range(0, len(tool_result), chunk_size):
                    yield tool_result[i:i + chunk_size]
                return
            # tool_result 为空时降级到流式阶段
        except Exception:
            # 工具调用失败（如模型不支持），降级为普通对话
            pass

    # 第二阶段：流式输出最终回复（无工具调用或工具调用降级）
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
