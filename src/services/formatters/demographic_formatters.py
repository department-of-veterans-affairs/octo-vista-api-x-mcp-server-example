"""Formatters for demographic data."""

from typing import Any


def format_phone(phone: str) -> str:
    """Format phone number for display.

    Args:
        phone: Raw phone number string

    Returns:
        Formatted phone number (e.g., "(123) 456-7890")
    """
    if not phone:
        return ""

    # Remove non-digits
    digits = "".join(c for c in phone if c.isdigit())

    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 7:
        return f"{digits[:3]}-{digits[3:]}"
    else:
        return phone


def format_ssn(ssn: Any) -> str:
    """Format SSN with masking for privacy.

    Args:
        ssn: Social Security Number

    Returns:
        Masked SSN (e.g., "***-**-1234")
    """
    if not ssn:
        return "***-**-****"

    ssn_str = str(ssn)
    # If it's already masked, return as is
    if "***" in ssn_str:
        return ssn_str

    # Remove any non-digit characters
    digits = "".join(c for c in ssn_str if c.isdigit())

    # Mask first 5 digits, show last 4
    if len(digits) >= 9:
        return f"***-**-{digits[-4:]}"
    else:
        return "***-**-****"
