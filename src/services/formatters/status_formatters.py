"""Formatters for status and urgency data."""


def format_status(status: str) -> str:
    """Convert status to lowercase.

    Args:
        status: The status value from VistA

    Returns:
        Formatted status in lowercase
    """
    if not status:
        return "unknown"
    return status.lower()


def format_urgency(urgency: str) -> str:
    """Convert urgency to lowercase.

    Args:
        urgency: The urgency value from VistA

    Returns:
        Formatted urgency in lowercase
    """
    if not urgency:
        return "routine"
    return urgency.lower()
