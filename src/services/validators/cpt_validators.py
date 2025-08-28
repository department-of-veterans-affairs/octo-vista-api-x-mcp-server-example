"""CPT Code validators and categorizers"""

import re

from ...utils import get_logger

logger = get_logger(__name__)


def validate_cpt_code(cpt_code: str) -> bool:
    """
    Validate CPT code format

    Args:
        cpt_code: CPT code to validate

    Returns:
        True if valid CPT code format
    """
    if not cpt_code:
        return False

    # Basic format check: 5 digits
    if re.match(r"^\d{5}$", cpt_code):
        return True

    # Allow some flexibility for newer formats
    return bool(re.match(r"^\d{4}[0-9A-Z]$", cpt_code))
