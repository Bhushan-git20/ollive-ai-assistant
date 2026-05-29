import re
from tools.calculator import calculate, TOOL_DEFINITION as CALC_DEF
from tools.datetime_tool import get_datetime_info, TOOL_DEFINITION as DT_DEF

def _has_math_expression(text: str) -> bool:
    """Detect if the message contains an inline math expression."""
    return bool(re.search(r'\d+\s*[\+\-\*\/\%\^]\s*\d+', text))

def route_tool(user_message: str) -> tuple[str | None, str | None]:
    """
    Check if the user message should trigger a tool.
    Returns: (tool_name, tool_result) or (None, None)
    """
    msg_lower = user_message.lower()

    # Datetime check
    for kw in DT_DEF["trigger_keywords"]:
        if kw in msg_lower:
            result = get_datetime_info(user_message)
            return "datetime", result

    # Calculator check — keyword OR inline expression
    has_calc_kw = any(kw in msg_lower for kw in CALC_DEF["trigger_keywords"])
    has_expr = _has_math_expression(user_message)

    if has_calc_kw or has_expr:
        # Try to extract math expression from message
        expr_match = re.search(r'[\d\s\+\-\*\/\%\^\(\)\.]+', user_message)
        if expr_match:
            expr = expr_match.group().strip()
            if re.search(r'\d', expr) and re.search(r'[\+\-\*\/]', expr):
                result = calculate(expr)
                return "calculator", result

    return None, None
