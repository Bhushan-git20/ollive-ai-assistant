"""Unit tests for OOP tool classes (BaseTool, CalculatorTool, DatetimeTool, WebSearchTool, ToolRouter)."""

from unittest.mock import patch

import pytest

from tools.base import BaseTool
from tools.calculator import CalculatorTool
from tools.datetime_tool import DatetimeTool
from tools.tool_router import ToolRouter
from tools.web_search import WebSearchTool


class TestBaseTool:
    def test_base_tool_is_abstract(self):
        with pytest.raises(TypeError):
            BaseTool()  # type: ignore[abstract]

    @pytest.mark.parametrize("tool_cls", [CalculatorTool, DatetimeTool, WebSearchTool])
    def test_tools_inherit_from_base_tool(self, tool_cls):
        tool = tool_cls()
        assert isinstance(tool, BaseTool)
        definition = tool.to_definition()
        assert definition["name"] == tool.name
        assert definition["description"] == tool.description
        assert isinstance(definition["trigger_keywords"], list)


class TestCalculatorTool:
    def test_can_handle_math_queries(self):
        calc = CalculatorTool()
        assert calc.can_handle("2 + 2") is True
        assert calc.can_handle("calculate 12 * 8") is True
        assert calc.can_handle("compute (10 + 5) * 2") is True

    def test_cannot_handle_non_math_queries(self):
        calc = CalculatorTool()
        assert calc.can_handle("what is the capital of France?") is False
        assert calc.can_handle("tell me a joke") is False
        assert calc.can_handle("") is False

    def test_run_evaluates_arithmetic(self):
        calc = CalculatorTool()
        assert "= 15" in calc.run("10 + 5")
        assert "= 42" in calc.run("calculate 6 * 7")
        assert "= 30" in calc.run("(10 + 5) * 2")
        assert "= -5" in calc.run("-10 + 5")

    def test_run_handles_division_by_zero(self):
        calc = CalculatorTool()
        result = calc.run("10 / 0")
        assert "zero" in result.lower()

    def test_run_rejects_unsafe_expression(self):
        calc = CalculatorTool()
        result = calc.run("__import__('os').system('echo hi')")
        assert "error" in result.lower()


class TestDatetimeTool:
    def test_can_handle_datetime_queries(self):
        dt = DatetimeTool()
        assert dt.can_handle("what time is it?") is True
        assert dt.can_handle("what is the date today?") is True
        assert dt.can_handle("what year is it?") is True

    def test_does_not_false_trigger_on_weekdays_or_compound_words(self):
        dt = DatetimeTool()
        assert dt.can_handle("Let's meet on Monday") is False
        assert dt.can_handle("It is my birthday") is False
        assert dt.can_handle("Going on holiday") is False

    def test_run_returns_utc_ist_and_unix(self):
        dt = DatetimeTool()
        output = dt.run()
        assert "UTC" in output
        assert "IST" in output
        assert "Unix:" in output


class TestWebSearchTool:
    def test_can_handle_search_queries(self):
        search = WebSearchTool()
        assert search.can_handle("search for FastAPI docs") is True
        assert search.can_handle("who is Ada Lovelace?") is True
        assert search.can_handle("what is quantum computing?") is True
        assert search.can_handle("hello world") is False

    def test_run_formats_results(self):
        search = WebSearchTool(max_results=2)
        fake_results = [
            {"title": "FastAPI", "body": "Modern web framework", "href": "https://fastapi.tiangolo.com"},
        ]
        with patch("tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.text.return_value = fake_results
            output = search.run("FastAPI")
        assert "[1] FastAPI" in output
        assert "https://fastapi.tiangolo.com" in output

    def test_run_handles_empty_and_errors(self):
        search = WebSearchTool()
        with patch("tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.text.return_value = []
            assert "No web search results found" in search.run("nothing")

        with patch("tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.text.side_effect = RuntimeError("network error")
            assert "Web search failed" in search.run("anything")


class TestToolRouterClass:
    def test_router_prioritizes_calculator_over_web_search_for_math(self):
        router = ToolRouter()
        name, result = router.route("what is 10 + 5?")
        assert name == "calculator"
        assert result is not None and "15" in result

    def test_router_routes_web_search(self):
        router = ToolRouter()
        with patch("tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.text.return_value = [
                {"title": "Ada", "body": "First programmer", "href": "https://example.com"}
            ]
            name, result = router.route("who is Ada Lovelace?")
        assert name == "web_search"
        assert "Ada" in (result or "")

    def test_router_returns_none_for_general_prompt(self):
        router = ToolRouter()
        assert router.route("Tell me a joke") == (None, None)
