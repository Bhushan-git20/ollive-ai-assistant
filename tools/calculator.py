import ast
import operator

# Safe operators only — no eval() on arbitrary code
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op = _OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {node.op}")
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op = _OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {node.op}")
        return op(operand)
    else:
        raise ValueError(f"Unsupported expression: {node}")

def calculate(expression: str) -> str:
    """
    Safely evaluate a math expression string.
    Returns result as string, or error message.
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree.body)
        # Round floats to avoid floating-point noise
        if isinstance(result, float):
            result = round(result, 10)
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return "Error: Division by zero."
    except Exception as e:
        return f"Error evaluating expression: {e}"

TOOL_DEFINITION = {
    "name": "calculator",
    "description": "Evaluate a mathematical expression. Input must be a plain math expression like '2 + 2' or '(10 * 3) / 2'.",
    "trigger_keywords": ["calculate", "compute", "solve", "math", "+", "-", "*", "/", "^", "%"],
}
