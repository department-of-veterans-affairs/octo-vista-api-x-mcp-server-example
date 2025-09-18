"""Validators for VistA-specific identifiers."""

import re


def validate_station(station: str) -> bool:
    """Validate station number format.

    Args:
        station: Station identifier

    Returns:
        True if valid, False otherwise
    """
    if not station:
        return False
    # Station should be 3 digits, optionally followed by division suffix
    return len(station) >= 3 and station[:3].isdigit()


def validate_duz(duz: str) -> bool:
    """Validate DUZ (user identifier) format.

    Args:
        duz: User identifier

    Returns:
        True if valid, False otherwise
    """
    if not duz:
        return False
    # DUZ should be numeric
    return duz.isdigit()


def validate_dfn(dfn: str) -> bool:
    """Validate DFN (patient identifier) format.

    Args:
        dfn: Patient identifier

    Returns:
        True if valid, False otherwise
    """
    if not dfn:
        return False
    # DFN should be numeric
    return dfn.isdigit()


def validate_icn(icn: str) -> bool:
    """Validate ICN (patient identifier) format.

    Args:
        icn: Patient identifier

    Returns:
        True if valid, False otherwise
    """
    return re.match(r"^(\d{16}|\d{9,10})V(\d{12}|\d{6})$", str(icn)) is not None
