"""Location code mapping utilities for VistA visit data"""

from typing import Any

from ...utils import get_logger

logger = get_logger(__name__)


class LocationMapper:
    """Utility for mapping and standardizing VistA location codes"""

    # Standard location type mappings
    LOCATION_TYPES = {
        # Inpatient units
        "WARD": "inpatient",
        "UNIT": "inpatient",
        "FLOOR": "inpatient",
        "ICU": "inpatient",
        "CCU": "inpatient",
        "STEPDOWN": "inpatient",
        "TELEMETRY": "inpatient",
        "MEDSURG": "inpatient",
        "ONCOLOGY": "inpatient",
        "CARDIAC": "inpatient",
        "NEURO": "inpatient",
        "ORTHO": "inpatient",
        "PEDIATRIC": "inpatient",
        "MATERNITY": "inpatient",
        "NURSERY": "inpatient",
        # Emergency/Critical care
        "ER": "emergency",
        "EMERGENCY": "emergency",
        "TRAUMA": "emergency",
        "URGENT": "emergency",
        "CRITICAL": "emergency",
        # Surgery
        "OR": "surgery",
        "OPERATING": "surgery",
        "SURGERY": "surgery",
        "PREOP": "surgery",
        "POSTOP": "surgery",
        "RECOVERY": "surgery",
        "PACU": "surgery",
        # Observation
        "OBS": "observation",
        "OBSERVATION": "observation",
        "SHORT": "observation",
        "HOLDING": "observation",
        # Outpatient
        "CLINIC": "outpatient",
        "AMBULATORY": "outpatient",
        "OUTPATIENT": "outpatient",
        "SPECIALTY": "outpatient",
        "PRIMARY": "outpatient",
        "CONSULT": "outpatient",
        "LAB": "outpatient",
        "RADIOLOGY": "outpatient",
        "PHARMACY": "outpatient",
        "PHYSICAL": "outpatient",
        "OCCUPATIONAL": "outpatient",
        "MENTAL": "outpatient",
        "PSYCH": "outpatient",
        "DENTAL": "outpatient",
        "OPTOMETRY": "outpatient",
        "AUDIOLOGY": "outpatient",
        "DIETARY": "outpatient",
        "SOCIAL": "outpatient",
        "SPEECH": "outpatient",
        "RESPIRATORY": "outpatient",
        "CARDIOLOGY": "outpatient",
        "DERMATOLOGY": "outpatient",
        "ENDOCRINOLOGY": "outpatient",
        "GASTROENTEROLOGY": "outpatient",
        "HEMATOLOGY": "outpatient",
        "INFECTIOUS": "outpatient",
        "NEPHROLOGY": "outpatient",
        "NEUROLOGY": "outpatient",
        "OPHTHALMOLOGY": "outpatient",
        "ORTHOPEDICS": "outpatient",
        "OTOLARYNGOLOGY": "outpatient",
        "PEDIATRICS": "outpatient",
        "PULMONOLOGY": "outpatient",
        "RHEUMATOLOGY": "outpatient",
        "UROLOGY": "outpatient",
        "VASCULAR": "outpatient",
    }

    # Standard location name mappings
    LOCATION_NAMES = {
        # Common abbreviations
        "ER": "Emergency Room",
        "ICU": "Intensive Care Unit",
        "CCU": "Coronary Care Unit",
        "OR": "Operating Room",
        "PACU": "Post-Anesthesia Care Unit",
        "OBS": "Observation Unit",
        "MEDSURG": "Medical-Surgical Unit",
        "PREOP": "Pre-Operative Unit",
        "POSTOP": "Post-Operative Unit",
        "TELEMETRY": "Telemetry Unit",
        "STEPDOWN": "Step-Down Unit",
        "PSYCH": "Psychiatry Unit",
        "NEURO": "Neurology Unit",
        "ORTHO": "Orthopedics Unit",
        "CARDIAC": "Cardiac Unit",
        "ONCOLOGY": "Oncology Unit",
        "PEDIATRIC": "Pediatric Unit",
        "MATERNITY": "Maternity Unit",
        "NURSERY": "Nursery Unit",
        # Specialty clinics
        "PRIMARY": "Primary Care Clinic",
        "SPECIALTY": "Specialty Clinic",
        "CONSULT": "Consultation Clinic",
        "LAB": "Laboratory",
        "RADIOLOGY": "Radiology Department",
        "PHARMACY": "Pharmacy",
        "PHYSICAL": "Physical Therapy",
        "OCCUPATIONAL": "Occupational Therapy",
        "MENTAL": "Mental Health Clinic",
        "DENTAL": "Dental Clinic",
        "OPTOMETRY": "Optometry Clinic",
        "AUDIOLOGY": "Audiology Clinic",
        "DIETARY": "Dietary Services",
        "SOCIAL": "Social Work",
        "SPEECH": "Speech Therapy",
        "RESPIRATORY": "Respiratory Therapy",
    }

    # Location code to standardized name mappings
    LOCATION_CODES = {
        # Common VistA location codes
        "500": "Washington DC VAMC",
        "501": "Baltimore VAMC",
        "502": "Richmond VAMC",
        "503": "Hampton VAMC",
        "504": "Salem VAMC",
        "505": "Martinsburg VAMC",
        "506": "Beckley VAMC",
        "507": "Huntington VAMC",
        "508": "Clarksburg VAMC",
        "509": "Charleston VAMC",
        "510": "Roanoke VAMC",
        "511": "Danville VAMC",
        "512": "Lexington VAMC",
        "513": "Louisville VAMC",
        "514": "Cincinnati VAMC",
        "515": "Dayton VAMC",
        "516": "Cleveland VAMC",
        "517": "Pittsburgh VAMC",
        "518": "Erie VAMC",
        "519": "Altoona VAMC",
        "520": "Butler VAMC",
    }

    @classmethod
    def get_location_type(cls, location_code: str, location_name: str) -> str:
        """
        Get standardized location type based on code and name

        Args:
            location_code: VistA location code
            location_name: Location name

        Returns:
            Standardized location type (inpatient, outpatient, emergency, surgery, observation)
        """
        if not location_code or not location_name:
            return "unknown"

        # Normalize inputs
        code_upper = location_code.upper()
        name_upper = location_name.upper()

        # Priority order for matching (most specific first)
        priority_patterns = [
            # Surgery patterns (check first to avoid conflicts)
            ("OPERATING", "surgery"),
            ("OR", "surgery"),
            ("SURGERY", "surgery"),
            ("PREOP", "surgery"),
            ("POSTOP", "surgery"),
            ("RECOVERY", "surgery"),
            ("PACU", "surgery"),
            # Emergency patterns
            ("EMERGENCY", "emergency"),
            ("ER", "emergency"),
            ("TRAUMA", "emergency"),
            ("URGENT", "emergency"),
            ("CRITICAL", "emergency"),
            # Observation patterns
            ("OBSERVATION", "observation"),
            ("OBS", "observation"),
            ("SHORT", "observation"),
            ("HOLDING", "observation"),
            # Inpatient patterns
            ("WARD", "inpatient"),
            ("UNIT", "inpatient"),
            ("FLOOR", "inpatient"),
            ("ICU", "inpatient"),
            ("CCU", "inpatient"),
            ("STEPDOWN", "inpatient"),
            ("TELEMETRY", "inpatient"),
            ("MEDSURG", "inpatient"),
            ("ONCOLOGY", "inpatient"),
            ("CARDIAC", "inpatient"),
            ("NEURO", "inpatient"),
            ("ORTHO", "inpatient"),
            ("PEDIATRIC", "inpatient"),
            ("MATERNITY", "inpatient"),
            ("NURSERY", "inpatient"),
            # Outpatient patterns
            ("CLINIC", "outpatient"),
            ("AMBULATORY", "outpatient"),
            ("OUTPATIENT", "outpatient"),
            ("SPECIALTY", "outpatient"),
            ("PRIMARY", "outpatient"),
            ("CONSULT", "outpatient"),
            ("LAB", "outpatient"),
            ("RADIOLOGY", "outpatient"),
            ("PHARMACY", "outpatient"),
            ("PHYSICAL", "outpatient"),
            ("OCCUPATIONAL", "outpatient"),
            ("MENTAL", "outpatient"),
            ("PSYCH", "outpatient"),
            ("DENTAL", "outpatient"),
            ("OPTOMETRY", "outpatient"),
            ("AUDIOLOGY", "outpatient"),
            ("DIETARY", "outpatient"),
            ("SOCIAL", "outpatient"),
            ("SPEECH", "outpatient"),
            ("RESPIRATORY", "outpatient"),
            ("CARDIOLOGY", "outpatient"),
            ("DERMATOLOGY", "outpatient"),
            ("ENDOCRINOLOGY", "outpatient"),
            ("GASTROENTEROLOGY", "outpatient"),
            ("HEMATOLOGY", "outpatient"),
            ("INFECTIOUS", "outpatient"),
            ("NEPHROLOGY", "outpatient"),
            ("NEUROLOGY", "outpatient"),
            ("OPHTHALMOLOGY", "outpatient"),
            ("ORTHOPEDICS", "outpatient"),
            ("OTOLARYNGOLOGY", "outpatient"),
            ("PEDIATRICS", "outpatient"),
            ("PULMONOLOGY", "outpatient"),
            ("RHEUMATOLOGY", "outpatient"),
            ("UROLOGY", "outpatient"),
            ("VASCULAR", "outpatient"),
        ]

        # Check for matches in priority order
        for pattern, location_type in priority_patterns:
            # Check for exact word matches or standalone patterns
            if (
                pattern == code_upper
                or pattern in name_upper.split()
                or f" {pattern} " in f" {name_upper} "
                or name_upper.startswith(pattern + " ")
                or name_upper.endswith(" " + pattern)
            ):
                return location_type

        # Default to outpatient for most clinic-like locations
        if any(word in name_upper for word in ["CLINIC", "AMBULATORY", "OUTPATIENT"]):
            return "outpatient"

        return "unknown"

    @classmethod
    def standardize_location_name(cls, location_name: str) -> str:
        """
        Standardize location name using known mappings

        Args:
            location_name: Raw location name

        Returns:
            Standardized location name
        """
        if not location_name:
            return "Unknown Location"

        name_upper = location_name.upper()

        # Check for exact matches
        for abbrev, full_name in cls.LOCATION_NAMES.items():
            if abbrev == name_upper:
                return full_name

        # Check for partial matches
        for abbrev, full_name in cls.LOCATION_NAMES.items():
            if abbrev in name_upper:
                return full_name

        # Return original if no mapping found
        return location_name

    @classmethod
    def get_facility_name(cls, facility_code: str) -> str:
        """
        Get facility name from facility code

        Args:
            facility_code: VistA facility code

        Returns:
            Facility name
        """
        return cls.LOCATION_CODES.get(facility_code, f"Station {facility_code}")

    @classmethod
    def is_inpatient_location(cls, location_code: str, location_name: str) -> bool:
        """Check if location is inpatient"""
        return cls.get_location_type(location_code, location_name) == "inpatient"

    @classmethod
    def is_emergency_location(cls, location_code: str, location_name: str) -> bool:
        """Check if location is emergency"""
        return cls.get_location_type(location_code, location_name) == "emergency"

    @classmethod
    def is_surgery_location(cls, location_code: str, location_name: str) -> bool:
        """Check if location is surgery"""
        return cls.get_location_type(location_code, location_name) == "surgery"

    @classmethod
    def is_observation_location(cls, location_code: str, location_name: str) -> bool:
        """Check if location is observation"""
        return cls.get_location_type(location_code, location_name) == "observation"

    @classmethod
    def is_outpatient_location(cls, location_code: str, location_name: str) -> bool:
        """Check if location is outpatient"""
        return cls.get_location_type(location_code, location_name) == "outpatient"

    @classmethod
    def get_location_summary(
        cls, location_code: str, location_name: str
    ) -> dict[str, Any]:
        """
        Get comprehensive location information

        Args:
            location_code: VistA location code
            location_name: Location name

        Returns:
            Dictionary with location information
        """
        location_type = cls.get_location_type(location_code, location_name)
        standardized_name = cls.standardize_location_name(location_name)

        return {
            "code": location_code,
            "name": location_name,
            "standardized_name": standardized_name,
            "type": location_type,
            "is_inpatient": cls.is_inpatient_location(location_code, location_name),
            "is_emergency": cls.is_emergency_location(location_code, location_name),
            "is_surgery": cls.is_surgery_location(location_code, location_name),
            "is_observation": cls.is_observation_location(location_code, location_name),
            "is_outpatient": cls.is_outpatient_location(location_code, location_name),
        }
