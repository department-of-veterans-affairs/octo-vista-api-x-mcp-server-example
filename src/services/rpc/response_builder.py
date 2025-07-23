"""Helper functions for building standardized responses."""

from typing import Any


def build_success_response(
    success: bool = True,
    data: Any = None,
    metadata: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build a standardized success response.

    Args:
        success: Success flag
        data: Response data
        metadata: Response metadata
        **kwargs: Additional fields to include

    Returns:
        Standardized response dictionary
    """
    response: dict[str, Any] = {"success": success}

    if data is not None:
        response["data"] = data

    if metadata is not None:
        response["metadata"] = metadata

    # Add any additional fields
    response.update(kwargs)

    return response


def build_error_response(
    error: str,
    metadata: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build a standardized error response.

    Args:
        error: Error message
        metadata: Response metadata
        **kwargs: Additional fields to include

    Returns:
        Standardized error response dictionary
    """
    response = {
        "success": False,
        "error": error,
    }

    if metadata is not None:
        response["metadata"] = metadata

    # Add any additional fields
    response.update(kwargs)

    return response
