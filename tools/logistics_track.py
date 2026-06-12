"""物流追踪工具 - 根据快递单号查询物流信息（模拟数据）。

⚠️ 所有数据均为虚构，仅用于演示目的。
"""

from . import registry

# 模拟物流追踪数据（模拟数据，所有信息均为虚构）
LOGISTICS_DATA = {
    "SF1234567890": [
        {"time": "2024-01-03 18:30", "status": "已签收", "location": "北京市朝阳区示例路快递柜"},
        {"time": "2024-01-03 09:15", "status": "派送中", "location": "北京朝阳区示例派送站，派送员 王师傅 13800001111"},
        {"time": "2024-01-02 22:00", "status": "运输中", "location": "北京转运中心"},
        {"time": "2024-01-02 06:30", "status": "运输中", "location": "河北廊坊中转站"},
        {"time": "2024-01-01 20:00", "status": "运输中", "location": "广东广州发件仓"},
        {"time": "2024-01-01 15:00", "status": "已揽收", "location": "广东广州发货仓"},
    ],
    "YZ9876543210": [
        {"time": "2024-01-05 14:20", "status": "已签收", "location": "广州市天河区示例路驿站"},
        {"time": "2024-01-05 08:00", "status": "派送中", "location": "广州天河区派送站"},
        {"time": "2024-01-04 19:30", "status": "运输中", "location": "广州分拨中心"},
        {"time": "2024-01-03 12:00", "status": "已揽收", "location": "广东广州发货仓"},
    ],
    "SF5566778899": [
        {"time": "2024-01-08 16:00", "status": "退货签收", "location": "广东广州退货仓"},
        {"time": "2024-01-07 10:00", "status": "运输中", "location": "北京转运中心"},
        {"time": "2024-01-06 14:30", "status": "已揽收", "location": "北京市朝阳区示例路"},
    ],
    "YZ1122334455": [
        {"time": "2024-01-08 11:00", "status": "派送中", "location": "杭州西湖区派送站，派送员 李师傅 13800002222"},
        {"time": "2024-01-07 20:00", "status": "运输中", "location": "杭州分拨中心"},
        {"time": "2024-01-06 15:00", "status": "运输中", "location": "广东广州转运中心"},
        {"time": "2024-01-06 08:00", "status": "已揽收", "location": "广东广州发货仓"},
    ],
}


def query_logistics(tracking_number):
    """根据快递单号查询物流轨迹。

    Args:
        tracking_number: 快递单号，如 'SF1234567890'

    Returns:
        物流轨迹的字符串描述
    """
    records = LOGISTICS_DATA.get(tracking_number)
    if not records:
        return f"未查询到快递单号 '{tracking_number}' 的物流信息，请检查单号是否正确。"

    latest = records[0]
    lines = [f"快递单号: {tracking_number}\n", f"最新状态: {latest['status']}（{latest['time']}）\n", f"当前位置: {latest['location']}\n"]
    lines.append("物流轨迹:\n")
    for r in records:
        lines.append(f"  [{r['time']}] {r['status']} - {r['location']}")

    return "\n".join(lines)


registry.register(
    name="query_logistics",
    description="根据快递单号查询物流追踪信息，返回物流轨迹和时间线。当用户询问包裹到哪里了、快递进度、物流状态时使用。",
    parameters={
        "type": "object",
        "properties": {
            "tracking_number": {
                "type": "string",
                "description": "快递单号，例如 'SF1234567890'",
            }
        },
        "required": ["tracking_number"],
    },
    handler=query_logistics,
)
