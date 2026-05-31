"""DeepSeek API 客户端 - 封装对话和工具调用逻辑。"""

import json
import os
from openai import OpenAI
from tools.registry import get_all_tools, execute_tool

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-4ee6ffd170c84e669755e2224559bf6c")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

SYSTEM_PROMPT = (
    "你是一个有帮助的 AI 助手。你可以使用工具来获取实时信息。"
    "当需要使用工具时，请调用相应的函数。"
    "请用中文回复用户的问题。"
)


def _handle_tool_calls(messages):
    """处理工具调用循环。非流式，最多 5 轮。

    Args:
        messages: 对话消息列表（会被修改）

    Returns:
        str: AI 的最终回复内容，或错误信息
    """
    tools = get_all_tools()

    for _ in range(5):
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
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


def chat_stream(message, history=None):
    """流式对话接口。

    流程：
    1. 在非流式模式下处理所有工具调用循环
    2. 工具调用完成后，将最终回复流式 yield 给调用者

    Args:
        message: 用户最新消息
        history: 历史对话列表 [{"role": "user/assistant", "content": "..."}]

    Yields:
        str: AI 回复的增量文本
    """
    if history is None:
        history = []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": message},
    ]

    # 第一阶段：处理工具调用（非流式）
    final_content = _handle_tool_calls(messages)

    # 将工具调用相关的消息（assistant tool_calls + tool responses）加入 messages
    # 现在 messages 已经包含了所有工具调用的细节

    # 第二阶段：流式输出最终回复
    # 我们已经在 _handle_tool_calls 中得到了最终回复内容，
    # 但为了流式体验，我们用 stream 模式重新生成一次
    # （去掉最后一条 assistant 消息，因为它还没加入 messages）

    # 过滤掉工具调用相关的消息，只保留用户/助手对话
    clean_messages = [
        m for m in messages
        if m.get("tool_calls") is None and m.get("role") != "tool"
    ]

    # 用流式模式生成最终回复
    stream = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=clean_messages,
        stream=True,
    )

    accumulated = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            accumulated += delta
            yield delta
