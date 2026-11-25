"""Safe AST-based calculator tool."""

import ast
import operator
import re
from typing import ClassVar, Optional

from tools.base import BaseTool

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

_INLINE_MATH_PATTERN = re.compile(r"\d+\s*[\+\-\*\/\%\^]\s*\d+")
_EXTRACT_EXPR_PATTERN = re.compile(r"[\d\(][\d\s\+\-\*\/\%\^\(\)\.]*[\d\)]")


def _safe_eval(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op = _OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {node.op}")
        return op(left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op = _OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {node.op}")
        return op(operand)
    raise ValueError(f"Unsupported expression: {node}")


class CalculatorTool(BaseTool):
    """Tool that safely evaluates arithmetic expressions using Python AST."""

    name: ClassVar[str] = "calculator"
    description: ClassVar[str] = (
        "Evaluate a mathematical expression. Input must be a plain math "
        "expression like '2 + 2' or '(10 * 3) / 2'."
    )
    trigger_keywords: ClassVar[tuple[str, ...]] = (
        "calculate",
        "compute",
        "solve",
        "math",
        "+",
        "-",
        "*",
        "/",
        "^",
        "%",
    )

    def extract_expression(self, query: str) -> Optional[str]:
        """Extract an arithmetic expression from a natural-language query."""
        match = _EXTRACT_EXPR_PATTERN.search(query)
        if not match:
            return None
        expr = match.group().strip()
        if re.search(r"\d", expr) and re.search(r"[\+\-\*\/\%\^]", expr):
            return expr
        return None

    def can_handle(self, query: str) -> bool:
        """Return True when the query contains an extractable math expression."""
        if not query or not query.strip():
            return False
        msg_lower = query.lower()
        has_kw = any(
            re.search(rf"\b{re.escape(kw)}\b", msg_lower)
            for kw in ("calculate", "compute", "solve", "math")
        )
        has_expr = bool(_INLINE_MATH_PATTERN.search(query))
        if not (has_kw or has_expr):
            return False
        return self.extract_expression(query) is not None

    def run(self, query: str) -> str:
        """Evaluate the expression directly or extract it from a sentence."""
        stripped = query.strip()
        candidate = stripped
        if re.search(r"[a-zA-Z_]", stripped):
            extracted = self.extract_expression(stripped)
            if extracted:
                candidate = extracted

        try:
            tree = ast.parse(candidate, mode="eval")
            result = _safe_eval(tree.body)
            if isinstance(result, float):
                result = round(result, 10)
            return f"{candidate} = {result}"
        except ZeroDivisionError:
            return "Error: Division by zero."
        except Exception as exc:
            return f"Error evaluating expression: {exc}"


_default_calculator = CalculatorTool()
TOOL_DEFINITION = _default_calculator.to_definition()


def calculate(expression: str) -> str:
    """Safely evaluate a math expression string."""
    return _default_calculator.run(expression)
