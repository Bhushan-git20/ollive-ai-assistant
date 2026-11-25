"""Base class for all Ollive AI assistant tools."""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class BaseTool(ABC):
    """Abstract base class defining the contract for assistant tools."""

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    trigger_keywords: ClassVar[tuple[str, ...]] = ()

    @abstractmethod
    def can_handle(self, query: str) -> bool:
        """Return True if this tool can handle the given user query."""

    @abstractmethod
    def run(self, query: str) -> str:
        """Execute the tool for the given query and return a formatted result."""

    def to_definition(self) -> dict[str, Any]:
        """Return a serializable metadata dictionary for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "trigger_keywords": list(self.trigger_keywords),
        }
