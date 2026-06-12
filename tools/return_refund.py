"""退换货查询工具 - 根据退货单号或订单号查询退换货进度（模拟数据）。

⚠️ 所有数据均为虚构，仅用于演示目的。
"""

from . import registry

# 模拟退换货记录（模拟数据，所有信息均为虚构）
RETURNS = {
    "RET20240101001": {
        "return_no": "RET20240101001",
        "order_no": "ORD20240105005",
        "customer": "张示例",
        "reason": "商品质量问题",
        "type": "退货退款",
        "status": "退款已处理",
        "refund_amount": 599.00,
        "refund_method": "原路退回（支付宝）",
        "created_at": "2024-01-06 10:00:00",
        "updated_at": "2024-01-09 15:00:00",
        "remark": "退款已原路退回，预计1-3个工作日到账。",
    },
    "RET20240102002": {
        "return_no": "RET20240102002",
        "order_no": "ORD20240103003",
        "customer": "王示例",
        "reason": "七天无理由退货",
        "type": "仅退货",
        "status": "审核中",
        "refund_amount": 49.00,
        "refund_method": "支付宝",
        "created_at": "2024-01-08 14:30:00",
        "updated_at": "2024-01-08 14:30:00",
        "remark": "您的退货申请已提交，我们将在24小时内审核。",
    },
    "RET20240103003": {
        "return_no": "RET20240103003",
        "order_no": "ORD20240101001",
        "customer": "张示例",
        "reason": "商品与描述不符",
        "type": "换货",
        "status": "同意换货",
        "refund_amount": 0.00,
        "refund_method": "",
        "created_at": "2024-01-07 09:00:00",
        "updated_at": "2024-01-07 16:00:00",
        "remark": "换货申请已通过，请将原商品寄回，新商品将在收到退货后48小时内发出。",
    },
    "RET20240104004": {
        "return_no": "RET20240104004",
        "order_no": "ORD20240104004",
        "customer": "赵示例",
        "reason": "拍错规格",
        "type": "退货退款",
        "status": "已退货待审核",
        "refund_amount": 318.00,
        "refund_method": "原路退回（微信支付）",
        "created_at": "2024-01-09 11:20:00",
        "updated_at": "2024-01-10 08:00:00",
        "remark": "我们已收到您的退货商品，正在审核中，预计1个工作日内完成。",
    },
}


def query_return_refund(return_number):
    """根据退货单号查询退换货进度。

    Args:
        return_number: 退货单号，如 'RET20240101001'

    Returns:
        退换货信息的字符串描述
    """
    record = RETURNS.get(return_number)
    if not record:
        return f"未找到退货单号为 '{return_number}' 的记录，请检查退货单号是否正确。"

    lines = [
        f"退货单号: {record['return_no']}",
        f"关联订单: {record['order_no']}",
        f"客户: {record['customer']}",
        f"类型: {record['type']}",
        f"原因: {record['reason']}",
        f"状态: {record['status']}",
        f"申请时间: {record['created_at']}",
        f"更新时间: {record['updated_at']}",
    ]
    if record["refund_amount"] > 0:
        lines.append(f"退款金额: ¥{record['refund_amount']:.2f}")
        lines.append(f"退款方式: {record['refund_method']}")
    lines.append(f"备注: {record['remark']}")

    return "\n".join(lines)


registry.register(
    name="query_return_refund",
    description="根据退货单号查询退换货进度，包括退货状态、退款金额、退款方式等。当用户询问退换货进度、退款什么时候到账时使用。",
    parameters={
        "type": "object",
        "properties": {
            "return_number": {
                "type": "string",
                "description": "退货单号，例如 'RET20240101001'",
            }
        },
        "required": ["return_number"],
    },
    handler=query_return_refund,
)
