"""CPT Code validators and categorizers"""

import re
from typing import Any

from ...utils import get_logger

logger = get_logger(__name__)


def categorize_cpt_code(cpt_code: str, description: str = "") -> str:
    """
    Categorize CPT code by procedure type

    Args:
        cpt_code: The CPT procedure code
        description: Procedure description

    Returns:
        Category string: surgery, diagnostic, evaluation, therapy, etc.
    """
    if not cpt_code:
        return "unknown"

    # Check description first for more specific categorization
    if description:
        desc_lower = description.lower()

        if any(word in desc_lower for word in ["surgery", "surgical", "operation"]):
            return "surgery"
        elif any(
            word in desc_lower
            for word in ["x-ray", "ct", "mri", "ultrasound", "imaging", "radiologic"]
        ):
            return "radiology"
        elif any(
            word in desc_lower
            for word in ["lab", "test", "specimen", "biopsy", "pathology"]
        ):
            return "pathology"
        elif any(
            word in desc_lower for word in ["therapy", "treatment", "rehabilitation"]
        ):
            return "therapy"
        elif any(
            word in desc_lower
            for word in ["evaluation", "exam", "consultation", "assessment"]
        ):
            return "evaluation"

    # Fall back to standard CPT code ranges
    try:
        code_num = int(cpt_code)
    except (ValueError, TypeError):
        return "unknown"

    if 10000 <= code_num <= 69999:
        return "surgery"
    elif 70000 <= code_num <= 79999:
        return "radiology"
    elif 80000 <= code_num <= 89999:
        return "pathology"
    elif 90000 <= code_num <= 99999:
        return "evaluation"
    elif 0 <= code_num <= 9999:
        return "category_i"

    return "other"


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


def parse_cpt_modifiers(modifier_string: str) -> list[str]:
    """
    Parse CPT modifiers from string

    Args:
        modifier_string: String containing modifiers

    Returns:
        List of parsed modifiers
    """
    if not modifier_string:
        return []

    # Common separator patterns
    separators = [",", ";", "|", " "]
    modifiers = [modifier_string]

    for sep in separators:
        temp_list = []
        for mod in modifiers:
            temp_list.extend(mod.split(sep))
        modifiers = temp_list

    # Clean and validate modifiers
    cleaned_modifiers = []
    for mod in modifiers:
        mod = mod.strip().upper()
        # CPT modifiers are typically 2 characters
        if re.match(r"^[A-Z0-9]{2}$", mod):
            cleaned_modifiers.append(mod)

    return cleaned_modifiers


def get_procedure_complexity(cpt_code: str, description: str = "") -> str:
    """
    Determine procedure complexity level

    Args:
        cpt_code: The CPT procedure code
        description: Procedure description

    Returns:
        Complexity level: "low", "moderate", "high"
    """
    if not cpt_code:
        return "moderate"

    try:
        code_num = int(cpt_code)
    except (ValueError, TypeError):
        return "moderate"

    # Surgery complexity based on CPT ranges
    if 10000 <= code_num <= 69999:
        if 10021 <= code_num <= 19499:  # Integumentary
            return "low"
        elif 20000 <= code_num <= 29999:  # Musculoskeletal
            return "moderate"
        elif 30000 <= code_num <= 39999:  # Respiratory/Cardiovascular
            return "high"
        elif 40000 <= code_num <= 49999 or 50000 <= code_num <= 59999:  # Digestive
            return "moderate"
        elif 60000 <= code_num <= 69999:  # Endocrine/Nervous
            return "high"

    # Radiology/imaging generally moderate complexity
    elif 70000 <= code_num <= 79999:
        return "moderate"

    # Lab tests generally low complexity
    elif 80000 <= code_num <= 89999:
        return "low"

    # E&M codes vary by complexity
    elif 90000 <= code_num <= 99999:
        if code_num in [99201, 99202, 99211, 99212]:  # Simple visits
            return "low"
        elif code_num in [99203, 99213, 99214]:  # Moderate visits
            return "moderate"
        elif code_num in [99204, 99205, 99215]:  # Complex visits
            return "high"

    # Check description for complexity indicators
    if description:
        desc_lower = description.lower()

        if any(
            word in desc_lower for word in ["major", "complex", "extensive", "radical"]
        ):
            return "high"
        elif any(
            word in desc_lower for word in ["minor", "simple", "limited", "brief"]
        ):
            return "low"
        elif any(
            word in desc_lower for word in ["intermediate", "moderate", "standard"]
        ):
            return "moderate"

    return "moderate"  # Default


def is_billable_procedure(cpt_code: str) -> bool:
    """
    Check if CPT code represents a billable procedure

    Args:
        cpt_code: The CPT procedure code

    Returns:
        True if procedure is typically billable
    """
    if not validate_cpt_code(cpt_code):
        return False

    try:
        code_num = int(cpt_code)
    except (ValueError, TypeError):
        return False

    # Most CPT codes are billable, but some are not
    non_billable_ranges = [
        # Some administrative codes
        (99000, 99009),  # Specimen handling
    ]

    return all(not start <= code_num <= end for start, end in non_billable_ranges)


def requires_prior_authorization(cpt_code: str, description: str = "") -> bool:
    """
    Check if procedure typically requires prior authorization

    Args:
        cpt_code: The CPT procedure code
        description: Procedure description

    Returns:
        True if prior auth is typically required
    """
    if not cpt_code:
        return False

    try:
        code_num = int(cpt_code)
    except (ValueError, TypeError):
        return False

    # High-cost procedure ranges that often require auth
    high_cost_ranges = [
        (20000, 29999),  # Major musculoskeletal
        (30000, 39999),  # Cardiothoracic
        (60000, 69999),  # Neurosurgery
        (70000, 74999),  # Advanced imaging
    ]

    for start, end in high_cost_ranges:
        if start <= code_num <= end:
            return True

    # Check description for high-cost indicators
    if description:
        desc_lower = description.lower()

        auth_keywords = [
            "transplant",
            "implant",
            "artificial",
            "prosthetic",
            "robotic",
            "laser",
            "microscopic",
            "endoscopic",
        ]

        if any(keyword in desc_lower for keyword in auth_keywords):
            return True

    return False


def get_procedure_duration_estimate(
    cpt_code: str, description: str = ""
) -> dict[str, Any]:
    """
    Estimate procedure duration based on CPT code

    Args:
        cpt_code: The CPT procedure code
        description: Procedure description

    Returns:
        Dictionary with duration estimates
    """
    if not cpt_code:
        return {"minutes": 0, "category": "unknown"}

    try:
        code_num = int(cpt_code)
    except (ValueError, TypeError):
        return {"minutes": 0, "category": "unknown"}

    # Duration estimates by CPT range (in minutes)
    if 10000 <= code_num <= 19999:  # Integumentary
        return {"minutes": 30, "category": "minor_surgery"}
    elif 20000 <= code_num <= 29999:  # Musculoskeletal
        return {"minutes": 90, "category": "major_surgery"}
    elif 30000 <= code_num <= 39999:  # Cardiovascular/Respiratory
        return {"minutes": 180, "category": "major_surgery"}
    elif 40000 <= code_num <= 49999:  # Digestive
        return {"minutes": 120, "category": "major_surgery"}
    elif 50000 <= code_num <= 59999:  # Urogenital
        return {"minutes": 90, "category": "major_surgery"}
    elif 60000 <= code_num <= 69999:  # Nervous/Endocrine
        return {"minutes": 240, "category": "major_surgery"}
    elif 70000 <= code_num <= 79999:  # Radiology
        return {"minutes": 45, "category": "imaging"}
    elif 80000 <= code_num <= 89999:  # Pathology/Lab
        return {"minutes": 5, "category": "lab_test"}
    elif 90000 <= code_num <= 99999:  # E&M
        if 99201 <= code_num <= 99205:  # New patient visits
            return {"minutes": 30, "category": "office_visit"}
        elif 99211 <= code_num <= 99215:  # Established patient visits
            return {"minutes": 20, "category": "office_visit"}
        else:
            return {"minutes": 15, "category": "consultation"}

    return {"minutes": 30, "category": "procedure"}  # Default
