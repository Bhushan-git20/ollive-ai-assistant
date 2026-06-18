from datetime import datetime, timezone

def get_datetime_info(query: str = "") -> str:
    """Return current UTC date/time info."""
    now_utc = datetime.now(timezone.utc)
    ist_offset = 5.5 * 3600
    from datetime import timedelta
    now_ist = now_utc + timedelta(seconds=ist_offset)

    return (
        f"Current date/time:\n"
        f"  UTC : {now_utc.strftime('%A, %d %B %Y %H:%M:%S')} UTC\n"
        f"  IST : {now_ist.strftime('%A, %d %B %Y %H:%M:%S')} IST\n"
        f"  Unix: {int(now_utc.timestamp())}"
    )

TOOL_DEFINITION = {
    "name": "datetime",
    "description": "Get the current date and time in UTC and IST.",
    "trigger_keywords": ["date", "time", "today", "now"],
}
