"""RPC execution services for VistA API calls."""

from .executor import execute_rpc
from .parameter_builder import (
    build_empty_params,
    build_multi_param,
    build_named_array_param,
    build_single_string_param,
)
from .response_builder import build_error_response, build_success_response

__all__ = [
    "execute_rpc",
    "build_single_string_param",
    "build_multi_param",
    "build_named_array_param",
    "build_empty_params",
    "build_success_response",
    "build_error_response",
]
