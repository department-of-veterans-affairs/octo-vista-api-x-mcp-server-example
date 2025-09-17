"""Vista RPC response parsers"""

from .legacy_parsers import (
    parse_fileman_date,
    parse_user_info,
)

__all__ = [
    "parse_fileman_date",
    "parse_user_info",
]
