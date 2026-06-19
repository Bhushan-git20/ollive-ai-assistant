import re
from tools.calculator import calculate, TOOL_DEFINITION as CALC_DEF
from tools.datetime_tool import get_datetime_info, TOOL_DEFINITION as DT_DEF
from tools.web_search import search_web, TOOL_DEFINITION as SEARCH_DEF

_DATETIME_PATTERN = re.compile(
    r'\b(date|time|today|now|year|month|when)\b|what (day|time) is it',
    re.IGNORECASE
)

def _triggers_datetime(text: str) -> bool:
    return bool(_DATETIME_PATTERN.search(text))

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
    if _triggers_datetime(msg_lower):
        result = get_datetime_info(user_message)
        return "datetime", result

    # Calculator check — keyword OR inline expression
    has_calc_kw = any(re.search(rf"\b{re.escape(kw)}\b", msg_lower) for kw in CALC_DEF["trigger_keywords"])
    has_expr = _has_math_expression(user_message)

    if has_calc_kw or has_expr:
        # Try to extract math expression from message
        expr_match = re.search(r'[\d\(][\d\s\+\-\*\/\%\^\(\)\.]*[\d\)]', user_message)
        if expr_match:
            expr = expr_match.group().strip()
            if re.search(r'\d', expr) and re.search(r'[\+\-\*\/]', expr):
                result = calculate(expr)
                return "calculator", result

    # Web Search check
    for kw in SEARCH_DEF["trigger_keywords"]:
        if re.search(rf"\b{re.escape(kw)}\b", msg_lower):
            result = search_web(user_message)
            return "web_search", result

    return None, None
