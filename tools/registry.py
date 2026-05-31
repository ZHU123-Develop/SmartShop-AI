"""工具注册中心 - 统一管理所有可被 AI 调用的工具。"""

_registry = {}


def register(name, description, parameters, handler):
    """注册一个工具。

    Args:
        name: 工具名称（如 get_weather）
        description: 工具描述（给 AI 看的，帮助它决定何时调用）
        parameters: JSON Schema 格式的参数字典
        handler: 实际执行的函数，接收 **kwargs，返回 str
    """
    _registry[name] = {
        "name": name,
        "description": description,
        "parameters": parameters,
        "handler": handler,
    }


def get_tool(name):
    """根据名称获取工具。"""
    return _registry.get(name)


def get_all_tools():
    """获取所有工具的 Function Calling 定义（供 DeepSeek API 使用）。"""
    return [
        {
            "type": "function",
            "function": {
                "name": info["name"],
                "description": info["description"],
                "parameters": info["parameters"],
            },
        }
        for info in _registry.values()
    ]


def execute_tool(name, **kwargs):
    """执行指定工具，返回结果字符串。"""
    tool = get_tool(name)
    if tool is None:
        return f"错误: 未知工具 '{name}'"
    try:
        return str(tool["handler"](**kwargs))
    except Exception as e:
        return f"工具 '{name}' 执行出错: {e}"
