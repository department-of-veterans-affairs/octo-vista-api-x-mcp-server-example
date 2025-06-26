"""Pydantic models for Vista data structures"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# Enums
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


# Base Models
class BaseVistaModel(BaseModel):
    """Base model for all Vista data models"""

    class Config:
        use_enum_values = True
        populate_by_name = True


# RPC Parameters
class RpcParameter(BaseModel):
    """RPC parameter structure"""

    string: str | None = None
    array: list[str] | None = None
    ref: str | None = None
    named_array: dict[str, str] | None = None


# Patient Models
class PatientSearchResult(BaseVistaModel):
    """Patient search result"""

    dfn: str = Field(..., description="Patient DFN (internal ID)")
    name: str = Field(..., description="Patient name (LAST,FIRST)")
    ssn_last_four: str = Field(..., description="Last 4 digits of SSN")
    date_of_birth: str | None = Field(None, description="Date of birth")
    gender: str | None = Field(None, description="Gender (M/F)")
    sensitive: bool = Field(False, description="Sensitive patient flag")
    station: str = Field(..., description="Station number")


class PatientDemographics(BaseVistaModel):
    """Detailed patient demographics"""

    dfn: str = Field(..., description="Patient DFN")
    name: str = Field(..., description="Full name")
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    ssn: str = Field(..., description="Masked SSN")
    date_of_birth: str
    age: int | None = None
    gender: str | None = None
    marital_status: str | None = None
    phone: str | None = None
    cell_phone: str | None = None
    email: str | None = None
    address: dict[str, str] | None = None
    emergency_contact: dict[str, str] | None = None
    insurance: list[dict[str, str]] | None = None
    veteran_status: dict[str, Any] | None = None
    station: str


# Clinical Models
class Medication(BaseVistaModel):
    """Medication information"""

    id: str | None = None
    name: str = Field(..., description="Medication name and strength")
    sig: str = Field(..., description="Dosing instructions")
    start_date: str | None = None
    stop_date: str | None = None
    status: str = Field(default="ACTIVE")
    quantity: str | None = None
    refills: int | None = None
    prescriber: str | None = None
    pharmacy: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Ensure status is uppercase"""
        return v.upper() if v else "ACTIVE"


class LabResult(BaseVistaModel):
    """Laboratory result"""

    id: str | None = None
    test_name: str
    value: str
    units: str | None = None
    reference_range: str | None = None
    flag: str | None = None
    status: str | None = None
    date_time: str
    ordering_provider: str | None = None

    @property
    def is_abnormal(self) -> bool:
        """Check if result is abnormal"""
        return bool(self.flag and self.flag in ["H", "L", "C", "A"])


class VitalSign(BaseVistaModel):
    """Vital sign measurement"""

    type: str = Field(..., description="Vital sign type (BP, P, R, T, WT, HT)")
    value: str
    units: str | None = None
    date_time: str
    qualifiers: str | None = None
    entered_by: str | None = None

    @property
    def display_name(self) -> str:
        """Get display name for vital type"""
        vital_names = {
            "BP": "Blood Pressure",
            "P": "Pulse",
            "R": "Respirations",
            "T": "Temperature",
            "WT": "Weight",
            "HT": "Height",
            "BMI": "Body Mass Index",
            "PN": "Pain Score",
            "PO2": "Pulse Oximetry",
        }
        return vital_names.get(self.type, self.type)


class Problem(BaseVistaModel):
    """Problem list entry"""

    id: str
    icd_code: str | None = None
    snomed_code: str | None = None
    description: str
    status: str = Field(default="ACTIVE")
    onset_date: str | None = None
    resolved_date: str | None = None
    type: str | None = None  # ACUTE/CHRONIC
    service_connected: bool = False
    priority: str | None = None


class Allergy(BaseVistaModel):
    """Allergy/adverse reaction"""

    id: str | None = None
    agent: str = Field(..., description="Allergen name")
    type: str | None = None
    reactions: list[str] = Field(default_factory=list)
    severity: str | None = None
    date_entered: str | None = None
    entered_by: str | None = None
    verified: bool = False
    comments: str | None = None


# Administrative Models
class Appointment(BaseVistaModel):
    """Appointment information"""

    appointment_ien: str
    patient_ien: str
    patient_name: str
    date_time: str
    clinic_ien: str
    clinic_name: str
    status: str
    provider: dict[str, str] | None = None
    check_in_time: str | None = None
    check_out_time: str | None = None
    type: str | None = None
    length: int | None = None  # minutes


class Provider(BaseVistaModel):
    """Provider/user information"""

    duz: str = Field(..., description="User DUZ")
    name: str
    title: str | None = None
    service: str | None = None
    phone: str | None = None
    pager: str | None = None
    email: str | None = None
    role: str | None = None
    active: bool = True
    station: str | None = None


class Station(BaseVistaModel):
    """Vista station information"""

    number: str = Field(..., description="Station number")
    name: str
    division: str | None = None
    timezone: str | None = None
    active: bool = True


# Response Models
class ToolResponse(BaseVistaModel):
    """Standard tool response format"""

    success: bool
    data: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

    @classmethod
    def success_response(cls, data: Any, metadata: dict[str, Any] | None = None):
        """Create a success response"""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def error_response(cls, error: str, metadata: dict[str, Any] | None = None):
        """Create an error response"""
        return cls(success=False, error=error, metadata=metadata)


class PatientSearchResponse(ToolResponse):
    """Patient search response"""

    search_term: str | None = None
    station: str | None = None
    count: int = 0
    patients: list[PatientSearchResult] = Field(default_factory=list)


class MedicationsResponse(ToolResponse):
    """Medications response"""

    patient_dfn: str
    station: str
    count: int = 0
    medications: list[Medication] = Field(default_factory=list)
    active_only: bool = True


class LabResultsResponse(ToolResponse):
    """Lab results response"""

    patient_dfn: str
    station: str
    count: int = 0
    lab_results: list[LabResult] = Field(default_factory=list)
    days_back: int | None = None


class VitalSignsResponse(ToolResponse):
    """Vital signs response"""

    patient_dfn: str
    station: str
    count: int = 0
    vital_signs: list[VitalSign] = Field(default_factory=list)
