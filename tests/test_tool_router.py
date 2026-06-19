"""
Unit tests for tools/tool_router.py

What we test:
- Datetime tool triggers on correct keywords with word boundaries
- Datetime tool does NOT false-trigger on day-of-week substrings
- Calculator triggers on math expressions and keywords
- Calculator does NOT trigger on non-math "what is" questions
- Neither tool triggers on generic queries
- Tool result format is correct
"""

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Datetime trigger tests
# ---------------------------------------------------------------------------

class TestDatetimeTriggers:

    def test_triggers_on_time_keyword(self):
        from tools.tool_router import route_tool
        name, result = route_tool("what time is it?")
        assert name == "datetime"
        assert result is not None

    def test_triggers_on_date_keyword(self):
        from tools.tool_router import route_tool
        name, result = route_tool("what is the date today?")
        assert name == "datetime"

    def test_triggers_on_today_keyword(self):
        from tools.tool_router import route_tool
        name, result = route_tool("what should I do today?")
        assert name == "datetime"

    def test_triggers_on_now_keyword(self):
        from tools.tool_router import route_tool
        name, result = route_tool("what time is it now?")
        assert name == "datetime"

    def test_triggers_on_when_keyword(self):
        from tools.tool_router import route_tool
        name, result = route_tool("when is the meeting?")
        assert name == "datetime"

    def test_triggers_on_year_keyword(self):
        from tools.tool_router import route_tool
        name, result = route_tool("what year is it?")
        assert name == "datetime"

    def test_triggers_on_month_keyword(self):
        from tools.tool_router import route_tool
        name, result = route_tool("what month is it?")
        assert name == "datetime"

    # --- FALSE POSITIVE TESTS (the main bug we fixed) ---

    def test_does_not_trigger_on_monday(self):
        """'day' substring in 'Monday' must NOT trigger datetime."""
        from tools.tool_router import route_tool
        name, result = route_tool("Let's meet on Monday")
        assert name != "datetime", "Monday should not trigger datetime tool"

    def test_does_not_trigger_on_tuesday(self):
        from tools.tool_router import route_tool
        name, result = route_tool("I'm free on Tuesday afternoon")
        assert name != "datetime"

    def test_does_not_trigger_on_wednesday(self):
        from tools.tool_router import route_tool
        name, result = route_tool("Wednesday works for me")
        assert name != "datetime"

    def test_does_not_trigger_on_thursday(self):
        from tools.tool_router import route_tool
        name, result = route_tool("Thursday is a holiday")
        assert name != "datetime"

    def test_does_not_trigger_on_friday(self):
        from tools.tool_router import route_tool
        name, result = route_tool("See you Friday")
        assert name != "datetime"

    def test_does_not_trigger_on_birthday(self):
        """'day' substring in 'birthday' must NOT trigger datetime."""
        from tools.tool_router import route_tool
        name, result = route_tool("It's my birthday next week")
        assert name != "datetime"

    def test_does_not_trigger_on_holiday(self):
        from tools.tool_router import route_tool
        name, result = route_tool("I'm on holiday this week")
        assert name != "datetime"

    def test_datetime_result_contains_utc(self):
        """Datetime result must include UTC and IST."""
        from tools.tool_router import route_tool
        name, result = route_tool("what time is it now?")
        assert "UTC" in result
        assert "IST" in result


# ---------------------------------------------------------------------------
# Calculator trigger tests
# ---------------------------------------------------------------------------

class TestCalculatorTriggers:

    def test_triggers_on_inline_math_expression(self):
        from tools.tool_router import route_tool
        name, result = route_tool("what is 10 + 5?")
        assert name == "calculator"
        assert "15" in result

    def test_triggers_on_multiplication(self):
        from tools.tool_router import route_tool
        name, result = route_tool("calculate 6 * 7")
        assert name == "calculator"
        assert "42" in result

    def test_triggers_on_division(self):
        from tools.tool_router import route_tool
        name, result = route_tool("100 / 4")
        assert name == "calculator"
        assert "25" in result

    def test_triggers_on_complex_expression(self):
        from tools.tool_router import route_tool
        name, result = route_tool("compute (10 + 5) * 2")
        assert name == "calculator"
        assert "30" in result

    def test_triggers_on_keyword_calculate(self):
        from tools.tool_router import route_tool
        name, result = route_tool("calculate 99 + 1")
        assert name == "calculator"

    def test_does_not_trigger_on_factual_what_is(self):
        """'what is' alone without math expression must NOT trigger calculator."""
        from tools.tool_router import route_tool
        name, result = route_tool("what is the capital of France?")
        assert name != "calculator"

    def test_does_not_trigger_on_plain_text(self):
        from tools.tool_router import route_tool
        name, result = route_tool("tell me a joke")
        assert name is None
        assert result is None

    def test_division_by_zero_handled(self):
        from tools.tool_router import route_tool
        name, result = route_tool("10 / 0")
        assert name == "calculator"
        assert "zero" in result.lower() or "error" in result.lower()


# ---------------------------------------------------------------------------
# No-tool tests
# ---------------------------------------------------------------------------

class TestNoToolTrigger:

    def test_generic_question_returns_none(self):
        from tools.tool_router import route_tool
        name, result = route_tool("Who wrote Harry Potter?")
        assert name is None
        assert result is None

    def test_greeting_returns_none(self):
        from tools.tool_router import route_tool
        name, result = route_tool("Hello!")
        assert name is None
        assert result is None

    def test_empty_string_returns_none(self):
        from tools.tool_router import route_tool
        name, result = route_tool("")
        assert name is None
        assert result is None
