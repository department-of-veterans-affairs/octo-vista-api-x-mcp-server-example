"""Helper functions for building RPC parameters."""

from typing import Any


def build_single_string_param(value: str) -> list[dict[str, Any]]:
    """Build parameters for a single string value.

    Args:
        value: The string value

    Returns:
        List with single string parameter
    """
    return [{"string": value}]


def build_named_array_param(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Build parameters for a named array.

    Args:
        params: Dictionary of named parameters

    Returns:
        List with named array parameter
    """
    return [{"namedArray": params}]


def build_icn_only_named_array_param(icn: str) -> list[dict[str, Any]]:
    """Build parameters for a named array.

    Args:
        icn: Patient ICN

    Returns:
        List with named array parameter
    """
    return [{"namedArray": {"patientId": f"; {icn}"}}]


def build_empty_params() -> list[dict[str, Any]]:
    """Build empty parameters list.

    Returns:
        Empty parameters list
    """
    return []


def build_multi_param(*values: str) -> list[dict[str, Any]]:
    """Build parameters for multiple string values.

    Args:
        *values: Variable number of string values

    Returns:
        List of string parameters
    """
    return [{"string": value} for value in values]
