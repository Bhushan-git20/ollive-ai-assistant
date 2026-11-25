"""Tool router dispatching queries to registered BaseTool instances."""

from typing import Optional, Sequence

from tools.base import BaseTool
from tools.calculator import CalculatorTool
from tools.datetime_tool import DatetimeTool
from tools.web_search import WebSearchTool


class ToolRouter:
    """Routes user queries to the first matching tool in priority order."""

    def __init__(self, tools: Optional[Sequence[BaseTool]] = None) -> None:
        self.tools: list[BaseTool] = (
            list(tools)
            if tools is not None
            else [DatetimeTool(), CalculatorTool(), WebSearchTool()]
        )

    def route(self, user_message: str) -> tuple[Optional[str], Optional[str]]:
        """Check registered tools and execute the first one that matches."""
        for tool in self.tools:
            if tool.can_handle(user_message):
                return tool.name, tool.run(user_message)
        return None, None


_default_router = ToolRouter()


def route_tool(user_message: str) -> tuple[Optional[str], Optional[str]]:
    """Check if the user message should trigger a tool."""
    return _default_router.route(user_message)
