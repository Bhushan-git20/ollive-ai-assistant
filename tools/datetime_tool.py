"""Datetime tool returning current UTC, IST, and Unix timestamps."""

import re
from datetime import datetime, timedelta, timezone
from typing import ClassVar

from tools.base import BaseTool

_DATETIME_PATTERN = re.compile(
    r"\b(date|time|today|now|year|month|when)\b|what (day|time) is it",
    re.IGNORECASE,
)


class DatetimeTool(BaseTool):
    """Tool that provides current UTC, IST, and Unix timestamp details."""

    name: ClassVar[str] = "datetime"
    description: ClassVar[str] = "Get the current date and time in UTC and IST."
    trigger_keywords: ClassVar[tuple[str, ...]] = ("date", "time", "today", "now")

    def can_handle(self, query: str) -> bool:
        """Return True if the query asks about current date or time."""
        if not query:
            return False
        return bool(_DATETIME_PATTERN.search(query))

    def run(self, query: str = "") -> str:
        """Return formatted UTC, IST, and Unix timestamp string."""
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc + timedelta(hours=5, minutes=30)
        return (
            f"Current date/time:\n"
            f"  UTC : {now_utc.strftime('%A, %d %B %Y %H:%M:%S')} UTC\n"
            f"  IST : {now_ist.strftime('%A, %d %B %Y %H:%M:%S')} IST\n"
            f"  Unix: {int(now_utc.timestamp())}"
        )


_default_datetime = DatetimeTool()
TOOL_DEFINITION = _default_datetime.to_definition()


def get_datetime_info(query: str = "") -> str:
    """Return current UTC/IST date/time info."""
    return _default_datetime.run(query)
