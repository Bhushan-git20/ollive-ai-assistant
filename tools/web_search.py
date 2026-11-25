"""DuckDuckGo web search tool."""

import re
from typing import ClassVar, Optional

from duckduckgo_search import DDGS

from tools.base import BaseTool


class WebSearchTool(BaseTool):
    """Tool that searches the web using DuckDuckGo."""

    name: ClassVar[str] = "web_search"
    description: ClassVar[str] = "Search the web for up-to-date information."
    trigger_keywords: ClassVar[tuple[str, ...]] = (
        "search",
        "lookup",
        "who is",
        "what is",
        "tell me about",
    )

    def __init__(self, max_results: int = 3) -> None:
        self.max_results = max_results

    def can_handle(self, query: str) -> bool:
        """Return True if the query includes a search trigger phrase."""
        if not query:
            return False
        msg_lower = query.lower()
        return any(
            re.search(rf"\b{re.escape(kw)}\b", msg_lower)
            for kw in self.trigger_keywords
        )

    def run(self, query: str, max_results: Optional[int] = None) -> str:
        """Perform a web search and return formatted top results."""
        limit = max_results if max_results is not None else self.max_results
        try:
            results = DDGS().text(query, max_results=limit)
            if not results:
                return "No web search results found."

            formatted_results = []
            for i, res in enumerate(results):
                title = res.get("title", "")
                body = res.get("body", "")
                href = res.get("href", "")
                formatted_results.append(f"[{i+1}] {title}\n{body}\nURL: {href}")

            return "\n\n".join(formatted_results)
        except Exception as exc:
            return f"Web search failed: {exc}"


_default_web_search = WebSearchTool()
TOOL_DEFINITION = _default_web_search.to_definition()


def search_web(query: str, max_results: int = 3) -> str:
    """Perform a web search and return a formatted string of the top results."""
    return _default_web_search.run(query, max_results=max_results)
