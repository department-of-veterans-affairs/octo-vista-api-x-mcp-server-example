from datetime import datetime


def format_datetime_for_mcp_response(dt: datetime | None) -> str | None:
    """Format datetime to ISO 8601 string with UTC timezone."""
    if dt is None:
        return None

    # Use explicit format string for ISO 8601 with UTC timezone and no microseconds
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def format_datetime_with_default(
    dt: datetime | None, default: datetime = datetime.min
) -> str:
    if default is None:
        raise ValueError("Default datetime cannot be None")

    formatted = format_datetime_for_mcp_response(dt)
    if formatted:
        return formatted
    formatted = format_datetime_for_mcp_response(default)
    if formatted:
        return formatted
    raise RuntimeError("Failed to format datetime")
