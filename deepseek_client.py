"""AI API 客户端 - 封装对话和工具调用逻辑。

支持通过 settings.json 或环境变量动态配置 API。
"""

import json
import os
from openai import OpenAI
from tools.registry import get_all_tools, execute_tool

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# 默认配置
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
    return api_key, base_url, model


def create_client():
    """根据当前配置创建 OpenAI 客户端。"""
    api_key, base_url, _ = get_config()
    if not api_key:
        raise RuntimeError("未配置 API Key，请在设置中填写")
    return OpenAI(api_key=api_key, base_url=base_url)


SYSTEM_PROMPT = (
    "你是一个有帮助的 AI 助手。你可以使用工具来获取实时信息。"
    "当需要使用工具时，请调用相应的函数。"
    "请用中文回复用户的问题。"
)


def _handle_tool_calls(messages, client, model):
    """处理工具调用循环。非流式，最多 5 轮。

    Args:
        messages: 对话消息列表（会被修改）
        client: OpenAI 客户端实例
        model: 模型名称

    Returns:
        str: AI 的最终回复内容，或错误信息
    """
    tools = get_all_tools()

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


def chat_stream(message, history=None):
    """流式对话接口。

    流程：
    1. 如果模型支持工具调用，在非流式模式下处理所有工具调用循环
    2. 工具调用完成后，将最终回复流式 yield 给调用者

    Args:
        message: 用户最新消息
        history: 历史对话列表 [{"role": "user/assistant", "content": "..."}]

    Yields:
        str: AI 回复的增量文本
    """
    if history is None:
        history = []

    api_key, base_url, model = get_config()
    client = create_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": message},
    ]

    # 第一阶段：处理工具调用（如果模型支持）
    if _supports_tool_calling(model):
        try:
            final_content = _handle_tool_calls(messages, client, model)

            # 过滤掉工具调用相关的消息，只保留用户/助手对话
            clean_messages = [
                m for m in messages
                if m.get("tool_calls") is None and m.get("role") != "tool"
            ]
        except Exception as e:
            # 工具调用失败（如模型不支持），降级为普通对话
            clean_messages = messages
    else:
        # 模型不支持工具调用，直接对话
        clean_messages = messages

    # 第二阶段：流式输出最终回复
    stream = client.chat.completions.create(
        model=model,
        messages=clean_messages,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
