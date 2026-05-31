"""天气查询工具 - 通过免费天气 API 查询实时天气。"""

import requests
from . import registry

# 使用 wttr.in 免费天气服务（无需 API Key）
WEATHER_API_URL = "https://wttr.in/{}?format=j1"


def get_weather(city):
    """查询指定城市的实时天气。

    Args:
        city: 城市名称，如 "北京", "Shanghai", "Tokyo"

    Returns:
        天气信息的字符串描述
    """
    try:
        resp = requests.get(WEATHER_API_URL.format(city), timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data["current_condition"][0]
        area = data["nearest_area"][0]
        city_name = area.get("areaName", [{}])[0].get("value", city)

        temp_c = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        wind_kmph = current["windspeedKmph"]

        return (
            f"{city_name} 当前天气:\n"
            f"  天气: {desc}\n"
            f"  温度: {temp_c}°C (体感 {feels_like}°C)\n"
            f"  湿度: {humidity}%\n"
            f"  风速: {wind_kmph} km/h"
        )
    except requests.exceptions.Timeout:
        return f"查询 {city} 天气超时，请稍后重试"
    except Exception as e:
        return f"查询天气失败: {e}"


registry.register(
    name="get_weather",
    description="查询指定城市的实时天气信息。",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "城市名称，如 '北京', 'Shanghai', 'Tokyo'",
            }
        },
        "required": ["city"],
    },
    handler=get_weather,
)
