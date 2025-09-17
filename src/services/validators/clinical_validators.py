"""Clinical data validation and categorization utilities with JSON-based configuration"""

# =============================================================================
# DIAGNOSIS-SPECIFIC VALIDATION FUNCTIONS
# =============================================================================


def validate_icd_code(icd_code: str, icd_version: str = "ICD-10") -> bool:
    """
    Validate ICD code format (ICD-9 or ICD-10).

    Args:
        icd_code: The ICD code to validate
        icd_version: "ICD-9" or "ICD-10"

    Returns:
        True if code format is valid
    """
    import re

    if not icd_code or not icd_version:
        return False

    icd_code = icd_code.strip().upper()

    if icd_version.upper() == "ICD-10":
        # ICD-10 format: Letter + 2-3 digits + optional decimal + alphanumeric extensions
        # Examples: A01, B95.1, C78.00, Z51.11, W21.00XD, S72.001A
        pattern = r"^[A-Z]\d{2,3}(\.[0-9A-Z]{1,4})?$"
        return re.match(pattern, icd_code) is not None

    elif icd_version.upper() == "ICD-9":
        # ICD-9 format: 3-5 digits with optional decimal, or V/E codes with 2-5 digits
        # Examples: 250, 250.0, 401.9, V58.69 (V + 2 digits), E879.3 (E + 3 digits)
        pattern = r"^([VE]\d{2,5}|\d{3,5})(\.\d{1,2})?$"
        return re.match(pattern, icd_code) is not None

    return False
