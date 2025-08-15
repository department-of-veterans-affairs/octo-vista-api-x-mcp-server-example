"""Common enums and base models used across the application"""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class BaseVistaModel(BaseModel):
    """Base model that excludes None values from serialization by default"""

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        strict=True,
        str_strip_whitespace=True,
    )

    def model_dump(self, **kwargs):
        """Override to exclude None values by default"""

        overrides = {
            "exclude_defaults": False,
            "exclude_none": True,
        }
        return super().model_dump(**(kwargs | overrides))


class Gender(str, Enum):
    """Patient gender values"""

    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"


class VprDomain(str, Enum):
    """VPR data domains"""

    PATIENT = "patient"
    ALLERGY = "allergy"
    MED = "med"
    LAB = "lab"
    VITAL = "vital"
    PROBLEM = "problem"
    APPOINTMENT = "appointment"
    DOCUMENT = "document"
    PROCEDURE = "procedure"
    CPT = "cpt"
    CONSULT = "consult"
    ORDER = "order"
    VISIT = "visit"
    SURGERY = "surgery"
    IMAGE = "image"
    IMMUNIZATION = "immunization"
    EDUCATION = "education"
    EXAM = "exam"
    FACTOR = "factor"


class MedicationStatus(str, Enum):
    """Medication status values"""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"
    DISCONTINUED = "DISCONTINUED"


class AllergyType(str, Enum):
    """Allergy types"""

    DRUG = "DRUG"
    FOOD = "FOOD"
    OTHER = "OTHER"
    ENVIRONMENTAL = "ENVIRONMENTAL"


class LabResultFlag(str, Enum):
    """Lab result flags"""

    HIGH = "H"
    LOW = "L"
    CRITICAL = "C"
    ABNORMAL = "A"
    NORMAL = ""
