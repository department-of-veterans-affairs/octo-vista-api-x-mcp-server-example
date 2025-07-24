"""Base models and common types for patient data"""

from enum import Enum
from typing import Optional, Protocol, runtime_checkable

from pydantic import BaseModel, field_validator


class BasePatientModel(BaseModel):
    """Base model for all patient data models"""

    model_config = {
        # Allow population by field name or alias
        "populate_by_name": True,
        # Use enum values
        "use_enum_values": True,
        # Serialize datetime as ISO format
        "json_schema_serialization_defaults_required": True,
    }


@runtime_checkable
class StatusEnum(Protocol):
    """Protocol for status enums that can be created from external values"""

    @classmethod
    def from_external_value(cls, value: str | None) -> "StatusEnum":
        """Create enum from external string value"""
        ...


class Gender(str, Enum):
    """Gender codes used in patient records"""

    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"

    @classmethod
    def from_code(cls, code: str) -> "Gender":
        """Create from gender code"""
        if not code:
            return cls.UNKNOWN

        code = code.upper()
        if code in ["M", "MALE"]:
            return cls.MALE
        elif code in ["F", "FEMALE"]:
            return cls.FEMALE
        else:
            return cls.UNKNOWN


class InterpretationCode(str, Enum):
    """Lab/vital interpretation codes (HL7 standard)"""

    HIGH = "H"
    LOW = "L"
    CRITICAL_HIGH = "HH"
    CRITICAL_LOW = "LL"
    ABNORMAL = "A"
    NORMAL = "N"

    @classmethod
    def from_hl7(cls, code: str | None) -> Optional["InterpretationCode"]:
        """Create from HL7 interpretation code"""
        if not code:
            return None

        # Extract the actual code from URN format
        if ":" in code:
            # e.g., "urn:hl7:observation-interpretation:H"
            parts = code.split(":")
            if len(parts) > 0:
                code = parts[-1]

        code = code.upper()

        # Map to our enum
        mapping = {
            "H": cls.HIGH,
            "L": cls.LOW,
            "HH": cls.CRITICAL_HIGH,
            "LL": cls.CRITICAL_LOW,
            "A": cls.ABNORMAL,
            "N": cls.NORMAL,
        }

        return mapping.get(code)


# Input validation enums for external data
class ConsultStatusInput(str, Enum):
    """Valid input values for consultation status"""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    COMPLETE = "COMPLETE"  # Alternative form
    CANCELLED = "CANCELLED"
    CANCELED = "CANCELED"  # Alternative spelling
    DISCONTINUED = "DISCONTINUED"


class UrgencyInput(str, Enum):
    """Valid input values for urgency levels"""

    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"
    EMERGENCY = "EMERGENCY"


class ConsultStatus(str, Enum):
    """Consultation status values"""

    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISCONTINUED = "DISCONTINUED"

    @classmethod
    def is_active(cls, status: str) -> bool:
        """Check if status indicates active consult"""
        return status in [cls.PENDING, cls.SCHEDULED, cls.ACTIVE]

    @classmethod
    def from_external_value(cls, value: str | None) -> "ConsultStatus":
        """Create from external status value with validation"""
        if not value:
            return cls.PENDING

        # Try to match against valid input enum first
        try:
            input_status = ConsultStatusInput(value.upper())
            # Map input enum to output enum
            mapping = {
                ConsultStatusInput.PENDING: cls.PENDING,
                ConsultStatusInput.SCHEDULED: cls.SCHEDULED,
                ConsultStatusInput.ACTIVE: cls.ACTIVE,
                ConsultStatusInput.COMPLETED: cls.COMPLETED,
                ConsultStatusInput.COMPLETE: cls.COMPLETED,  # Alternative form
                ConsultStatusInput.CANCELLED: cls.CANCELLED,
                ConsultStatusInput.CANCELED: cls.CANCELLED,  # Alternative spelling
                ConsultStatusInput.DISCONTINUED: cls.DISCONTINUED,
            }
            return mapping[input_status]
        except ValueError:
            # Fallback for unknown values
            return cls.PENDING

    @classmethod
    def from_name(cls, name: str) -> "ConsultStatus":
        """Legacy method - delegates to from_external_value"""
        return cls.from_external_value(name)


class Urgency(str, Enum):
    """Consultation urgency levels"""

    ROUTINE = "Routine"
    URGENT = "Urgent"
    STAT = "STAT"
    EMERGENCY = "Emergency"

    @classmethod
    def from_external_value(cls, value: str | None) -> "Urgency":
        """Create from external urgency value with validation"""
        if not value:
            return cls.ROUTINE

        # Try to match against valid input enum first
        try:
            input_urgency = UrgencyInput(value.upper())
            # Map input enum to output enum
            mapping = {
                UrgencyInput.ROUTINE: cls.ROUTINE,
                UrgencyInput.URGENT: cls.URGENT,
                UrgencyInput.STAT: cls.STAT,
                UrgencyInput.EMERGENCY: cls.EMERGENCY,
            }
            return mapping[input_urgency]
        except ValueError:
            # Fallback for unknown values
            return cls.ROUTINE

    @classmethod
    def from_name(cls, name: str) -> "Urgency":
        """Legacy method - delegates to from_external_value"""
        return cls.from_external_value(name)


class VitalType(str, Enum):
    """Common vital sign types"""

    BP = "BLOOD PRESSURE"
    TEMP = "TEMPERATURE"
    PULSE = "PULSE"
    RESP = "RESPIRATION"
    WEIGHT = "WEIGHT"
    HEIGHT = "HEIGHT"
    PAIN = "PAIN"
    O2_SAT = "PULSE OXIMETRY"


class StatusEnumFactory:
    """Factory for creating status enums with type safety"""

    @staticmethod
    def create_consult_status(value: str | ConsultStatusInput | None) -> ConsultStatus:
        """Create ConsultStatus with input validation"""
        if isinstance(value, ConsultStatusInput):
            return ConsultStatus.from_external_value(value.value)
        return ConsultStatus.from_external_value(value)

    @staticmethod
    def create_urgency(value: str | UrgencyInput | None) -> Urgency:
        """Create Urgency with input validation"""
        if isinstance(value, UrgencyInput):
            return Urgency.from_external_value(value.value)
        return Urgency.from_external_value(value)


class FacilityInfo(BasePatientModel):
    """Facility information"""

    code: str
    name: str

    @field_validator("code", mode="before")
    @classmethod
    def validate_code(cls, v):
        """Ensure code is string"""
        return str(v) if v is not None else ""


class CodedValue(BasePatientModel):
    """Generic coded value with code and name"""

    code: str
    name: str
    system: str | None = None

    @classmethod
    def from_code_name_pair(
        cls, code: str, name: str, system: str | None = None
    ) -> "CodedValue":
        """Create from code/name pair"""
        return cls(code=code, name=name, system=system)
