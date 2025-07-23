"""Validators and parsers for clinical data."""

from typing import Any


def parse_boolean(value: Any) -> bool:
    """Parse various boolean representations.

    Args:
        value: Value to parse as boolean

    Returns:
        Boolean representation of the value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.upper() in ["TRUE", "YES", "Y", "1", "ON"]
    return bool(value)
