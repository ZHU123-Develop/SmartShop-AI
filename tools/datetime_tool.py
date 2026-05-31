"""时间日期工具 - 获取当前时间和日期。"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from . import registry


def get_current_time(timezone_name=None):
    """获取当前时间/日期。

    Args:
        timezone_name: 可选，时区名称，如 'Asia/Shanghai', 'UTC', 'America/New_York'

    Returns:
        当前时间的字符串描述
    """
    try:
        if timezone_name:
            tz = ZoneInfo(timezone_name)
        else:
            tz = ZoneInfo("Asia/Shanghai")
        now = datetime.now(tz)
        return (
            f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}\n"
            f"时区: {tz.key}\n"
            f"星期: {['', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][now.weekday()]}"
        )
    except Exception as e:
        return f"获取时间失败: {e}"


registry.register(
    name="get_current_time",
    description="获取当前日期和时间。可指定时区。",
    parameters={
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "时区名称，如 'Asia/Shanghai', 'UTC', 'America/New_York'。默认为 Asia/Shanghai。",
            }
        },
        "required": [],
    },
    handler=get_current_time,
)
