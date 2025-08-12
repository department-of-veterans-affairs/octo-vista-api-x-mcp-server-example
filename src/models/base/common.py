"""Common enums and base models used across the application"""

from enum import Enum

from pydantic import BaseModel


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


class PaginationMetadata(BaseModel):
    """Enhanced pagination metadata with LLM guidance"""

    total: int
    returned: int
    offset: int
    limit: int
    has_more: bool
    next_offset: int | None = None
    suggested_next_call: str | None = None


class BaseVistaModel(BaseModel):
    """Base model for all Vista data models"""

    class Config:
        use_enum_values = True
        populate_by_name = True
