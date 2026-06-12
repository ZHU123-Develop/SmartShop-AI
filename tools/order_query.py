"""订单查询工具 - 根据订单号查询订单信息（模拟数据）。

⚠️ 所有数据均为虚构，仅用于演示目的。
"""

from . import registry

# 模拟订单数据库（模拟数据，所有信息均为虚构）
ORDERS = {
    "ORD20240101001": {
        "order_no": "ORD20240101001",
        "customer": "张示例",
        "status": "已发货",
        "items": [{"name": "iPhone 15 Pro 手机壳", "qty": 1, "price": 89.00}],
        "total": 89.00,
        "created_at": "2024-01-01 10:30:00",
        "shipping_no": "SF1234567890",
        "address": "北京市朝阳区示例路SOHO T3",
    },
    "ORD20240102002": {
        "order_no": "ORD20240102002",
        "customer": "李示例",
        "status": "待付款",
        "items": [{"name": "无线蓝牙耳机", "qty": 1, "price": 199.00}],
        "total": 199.00,
        "created_at": "2024-01-02 14:20:00",
        "shipping_no": "",
        "address": "上海市浦东新区示例环路1000号",
    },
    "ORD20240103003": {
        "order_no": "ORD20240103003",
        "customer": "王示例",
        "status": "已签收",
        "items": [
            {"name": "机械键盘 Cherry轴", "qty": 1, "price": 349.00},
            {"name": "键盘腕托", "qty": 1, "price": 49.00},
        ],
        "total": 398.00,
        "created_at": "2024-01-03 09:15:00",
        "shipping_no": "YZ9876543210",
        "address": "广州市天河区体育示例路58号",
    },
    "ORD20240104004": {
        "order_no": "ORD20240104004",
        "customer": "赵示例",
        "status": "已付款",
        "items": [{"name": "USB-C 扩展坞 7合1", "qty": 2, "price": 159.00}],
        "total": 318.00,
        "created_at": "2024-01-04 16:45:00",
        "shipping_no": "",
        "address": "深圳市南山区科技园示例路88号",
    },
    "ORD20240105005": {
        "order_no": "ORD20240105005",
        "customer": "张示例",
        "status": "已退货",
        "items": [{"name": "智能手表 运动版", "qty": 1, "price": 599.00}],
        "total": 599.00,
        "created_at": "2024-01-05 11:00:00",
        "shipping_no": "SF5566778899",
        "address": "北京市朝阳区示例路SOHO T3",
    },
    "ORD20240106006": {
        "order_no": "ORD20240106006",
        "customer": "孙示例",
        "status": "已发货",
        "items": [{"name": "笔记本电脑支架 铝合金", "qty": 1, "price": 129.00}],
        "total": 129.00,
        "created_at": "2024-01-06 08:30:00",
        "shipping_no": "YZ1122334455",
        "address": "杭州市西湖区示例路200号",
    },
}


def query_order(order_number):
    """根据订单号查询订单详情。

    Args:
        order_number: 订单号，如 'ORD20240101001'

    Returns:
        订单信息的字符串描述
    """
    order = ORDERS.get(order_number)
    if not order:
        return f"未找到订单号为 '{order_number}' 的订单，请检查订单号是否正确。"

    items_str = "\n".join(
        f"  - {item['name']} x{item['qty']}  ¥{item['price']:.2f}"
        for item in order["items"]
    )
    shipping = f"物流单号: {order['shipping_no']}" if order["shipping_no"] else "物流单号: 暂无"

    return (
        f"订单号: {order['order_no']}\n"
        f"客户: {order['customer']}\n"
        f"状态: {order['status']}\n"
        f"下单时间: {order['created_at']}\n"
        f"商品:\n{items_str}\n"
        f"合计: ¥{order['total']:.2f}\n"
        f"{shipping}\n"
        f"收货地址: {order['address']}"
    )


registry.register(
    name="query_order",
    description="根据订单号查询订单详情，包括订单状态、商品信息、收货地址、物流单号等。当用户提到订单号或询问订单状态时使用。",
    parameters={
        "type": "object",
        "properties": {
            "order_number": {
                "type": "string",
                "description": "订单号，例如 'ORD20240101001'",
            }
        },
        "required": ["order_number"],
    },
    handler=query_order,
)
