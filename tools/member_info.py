"""会员信息查询工具 - 根据手机号查询会员信息（模拟数据）。

⚠️ 所有数据均为虚构，仅用于演示目的。
"""

from . import registry

# 模拟会员数据库（模拟数据，所有信息均为虚构）
MEMBERS = {
    "13800000001": {
        "phone": "13800000001",
        "name": "张示例",
        "tier": "黄金会员",
        "points": 2580,
        "coupons": 3,
        "join_date": "2023-06-15",
        "total_spent": 8960.00,
        "benefits": "95折优惠、生日双倍积分、免费快递、专属客服",
    },
    "13800000002": {
        "phone": "13800000002",
        "name": "李示例",
        "tier": "普通会员",
        "points": 320,
        "coupons": 1,
        "join_date": "2024-01-02",
        "total_spent": 199.00,
        "benefits": "积分累计、优惠券领取",
    },
    "13800000003": {
        "phone": "13800000003",
        "name": "王示例",
        "tier": "白银会员",
        "points": 1250,
        "coupons": 2,
        "join_date": "2023-11-20",
        "total_spent": 3580.00,
        "benefits": "98折优惠、积分累计、生日双倍积分",
    },
    "13800000004": {
        "phone": "13800000004",
        "name": "赵示例",
        "tier": "钻石会员",
        "points": 15600,
        "coupons": 8,
        "join_date": "2022-03-10",
        "total_spent": 52000.00,
        "benefits": "88折优惠、生日三倍积分、免费快递、专属客服、新品优先购、年度礼盒",
    },
    "13800000005": {
        "phone": "13800000005",
        "name": "孙示例",
        "tier": "黄金会员",
        "points": 3200,
        "coupons": 4,
        "join_date": "2023-08-05",
        "total_spent": 12300.00,
        "benefits": "95折优惠、生日双倍积分、免费快递、专属客服",
    },
}

# 会员等级说明
TIER_RULES = """会员等级规则：
  - 普通会员：注册即享
  - 白银会员：累计消费满 ¥2,000
  - 黄金会员：累计消费满 ¥8,000
  - 钻石会员：累计消费满 ¥30,000

积分规则：
  - 每消费 ¥1 累积 1 积分
  - 100 积分 = ¥1 优惠券
  - 生日月消费双倍/三倍积分（视会员等级）"""


def query_member_info(phone_number):
    """根据手机号查询会员信息。

    Args:
        phone_number: 手机号码，如 '13800000001'

    Returns:
        会员信息的字符串描述
    """
    member = MEMBERS.get(phone_number)
    if not member:
        return (
            f"未查询到手机号 '{phone_number}' 的会员信息。\n"
            f"该手机号可能尚未注册为SmartShop会员。\n\n"
            f"{TIER_RULES}"
        )

    next_tier = {"普通会员": ("白银会员", 2000), "白银会员": ("黄金会员", 8000), "黄金会员": ("钻石会员", 30000)}.get(member["tier"], (None, None))
    next_info = ""
    if next_tier[0]:
        remaining = next_tier[1] - member["total_spent"]
        next_info = f"\n升级进度: 再消费 ¥{remaining:.2f} 即可升级为 {next_tier[0]}"

    return (
        f"会员姓名: {member['name']}\n"
        f"手机号: {member['phone']}\n"
        f"会员等级: {member['tier']}\n"
        f"累计积分: {member['points']} 分\n"
        f"可用优惠券: {member['coupons']} 张\n"
        f"累计消费: ¥{member['total_spent']:.2f}\n"
        f"注册时间: {member['join_date']}\n"
        f"会员权益: {member['benefits']}{next_info}"
    )


registry.register(
    name="query_member_info",
    description="根据手机号查询会员信息，包括会员等级、积分、优惠券数量、累计消费等。当用户询问会员权益、积分、等级时使用。",
    parameters={
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": "手机号码，例如 '13800000001'",
            }
        },
        "required": ["phone_number"],
    },
    handler=query_member_info,
)
