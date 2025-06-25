"""Pydantic models for Vista data structures"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

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
    string: Optional[str] = None
    array: Optional[List[str]] = None
    ref: Optional[str] = None
    namedArray: Optional[Dict[str, str]] = None


# Patient Models
class PatientSearchResult(BaseVistaModel):
    """Patient search result"""
    dfn: str = Field(..., description="Patient DFN (internal ID)")
    name: str = Field(..., description="Patient name (LAST,FIRST)")
    ssn_last_four: str = Field(..., description="Last 4 digits of SSN")
    date_of_birth: Optional[str] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender (M/F)")
    sensitive: bool = Field(False, description="Sensitive patient flag")
    station: str = Field(..., description="Station number")


class PatientDemographics(BaseVistaModel):
    """Detailed patient demographics"""
    dfn: str = Field(..., description="Patient DFN")
    name: str = Field(..., description="Full name")
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    ssn: str = Field(..., description="Masked SSN")
    date_of_birth: str
    age: Optional[int] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    phone: Optional[str] = None
    cell_phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    emergency_contact: Optional[Dict[str, str]] = None
    insurance: Optional[List[Dict[str, str]]] = None
    veteran_status: Optional[Dict[str, Any]] = None
    station: str


# Clinical Models
class Medication(BaseVistaModel):
    """Medication information"""
    id: Optional[str] = None
    name: str = Field(..., description="Medication name and strength")
    sig: str = Field(..., description="Dosing instructions")
    start_date: Optional[str] = None
    stop_date: Optional[str] = None
    status: str = Field(default="ACTIVE")
    quantity: Optional[str] = None
    refills: Optional[int] = None
    prescriber: Optional[str] = None
    pharmacy: Optional[str] = None
    
    @field_validator("status")
    def validate_status(cls, v):
        """Ensure status is uppercase"""
        return v.upper() if v else "ACTIVE"


class LabResult(BaseVistaModel):
    """Laboratory result"""
    id: Optional[str] = None
    test_name: str
    value: str
    units: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None
    status: Optional[str] = None
    date_time: str
    ordering_provider: Optional[str] = None
    
    @property
    def is_abnormal(self) -> bool:
        """Check if result is abnormal"""
        return bool(self.flag and self.flag in ["H", "L", "C", "A"])


class VitalSign(BaseVistaModel):
    """Vital sign measurement"""
    type: str = Field(..., description="Vital sign type (BP, P, R, T, WT, HT)")
    value: str
    units: Optional[str] = None
    date_time: str
    qualifiers: Optional[str] = None
    entered_by: Optional[str] = None
    
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
    icd_code: Optional[str] = None
    snomed_code: Optional[str] = None
    description: str
    status: str = Field(default="ACTIVE")
    onset_date: Optional[str] = None
    resolved_date: Optional[str] = None
    type: Optional[str] = None  # ACUTE/CHRONIC
    service_connected: bool = False
    priority: Optional[str] = None


class Allergy(BaseVistaModel):
    """Allergy/adverse reaction"""
    id: Optional[str] = None
    agent: str = Field(..., description="Allergen name")
    type: Optional[str] = None
    reactions: List[str] = Field(default_factory=list)
    severity: Optional[str] = None
    date_entered: Optional[str] = None
    entered_by: Optional[str] = None
    verified: bool = False
    comments: Optional[str] = None


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
    provider: Optional[Dict[str, str]] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    type: Optional[str] = None
    length: Optional[int] = None  # minutes


class Provider(BaseVistaModel):
    """Provider/user information"""
    duz: str = Field(..., description="User DUZ")
    name: str
    title: Optional[str] = None
    service: Optional[str] = None
    phone: Optional[str] = None
    pager: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    active: bool = True
    station: Optional[str] = None


class Station(BaseVistaModel):
    """Vista station information"""
    number: str = Field(..., description="Station number")
    name: str
    division: Optional[str] = None
    timezone: Optional[str] = None
    active: bool = True


# Response Models
class ToolResponse(BaseVistaModel):
    """Standard tool response format"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success_response(cls, data: Any, metadata: Optional[Dict[str, Any]] = None):
        """Create a success response"""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def error_response(cls, error: str, metadata: Optional[Dict[str, Any]] = None):
        """Create an error response"""
        return cls(success=False, error=error, metadata=metadata)


class PatientSearchResponse(ToolResponse):
    """Patient search response"""
    search_term: Optional[str] = None
    station: Optional[str] = None
    count: int = 0
    patients: List[PatientSearchResult] = Field(default_factory=list)


class MedicationsResponse(ToolResponse):
    """Medications response"""
    patient_dfn: str
    station: str
    count: int = 0
    medications: List[Medication] = Field(default_factory=list)
    active_only: bool = True


class LabResultsResponse(ToolResponse):
    """Lab results response"""
    patient_dfn: str
    station: str
    count: int = 0
    lab_results: List[LabResult] = Field(default_factory=list)
    days_back: Optional[int] = None


class VitalSignsResponse(ToolResponse):
    """Vital signs response"""
    patient_dfn: str
    station: str
    count: int = 0
    vital_signs: List[VitalSign] = Field(default_factory=list)