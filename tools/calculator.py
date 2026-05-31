"""计算器工具 - 安全地计算数学表达式。"""

import ast
import operator
from . import registry

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_node(node):
    """安全地求值 AST 节点。"""
    if isinstance(node, ast.Constant) and isinstance(node.n if hasattr(node, 'n') else node.value, (int, float)):
        return node.n if hasattr(node, 'n') else node.value
    if isinstance(node, ast.Num):  # Python < 3.8
        return node.n
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"不支持的操作: {op_type.__name__}")
        return _SAFE_OPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"不支持的操作: {op_type.__name__}")
        return _SAFE_OPS[op_type](operand)
    raise ValueError("不支持的表达式")


def calculate(expression):
    """计算数学表达式的结果。

    Args:
        expression: 数学表达式字符串，如 "2 + 3 * 4"

    Returns:
        计算结果的字符串
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        if isinstance(result, float):
            return f"{result:.6g}"
        return str(result)
    except ZeroDivisionError:
        return "错误: 除零"
    except Exception as e:
        return f"计算错误: {e}"


register(
    name="calculate",
    description="计算数学表达式的结果。支持加减乘除、幂运算。",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要计算的数学表达式，例如 '2 + 3 * 4'",
            }
        },
        "required": ["expression"],
    },
    handler=calculate,
)
