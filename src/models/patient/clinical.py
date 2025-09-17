"""Clinical data models for patient records"""

from datetime import UTC, datetime
from typing import Any

from pydantic import Field, field_serializer, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...services.parsers.patient.value_parser import (
    parse_blood_pressure,
)
from ...utils import get_logger
from ..utils import format_datetime_for_mcp_response, format_datetime_with_default
from .base import (
    BasePatientModel,
    ConsultStatus,
    InterpretationCode,
    ProvisionalDx,
    Urgency,
    VitalType,
)

# Import extracted models

logger = get_logger()


class VitalSign(BasePatientModel):
    """Vital sign measurement"""

    uid: str
    local_id: str = Field(alias="localId")

    # Measurement info
    type_code: str = Field(alias="typeCode")
    type_name: str = Field(alias="typeName")
    display_name: str = Field(alias="displayName")

    # Results - handle various formats
    result: str  # Original string value (e.g., "135/100")
    systolic: int | None = None  # For BP
    diastolic: int | None = None  # For BP
    units: str | None = None

    # Reference ranges
    high: float | str | None = None
    low: float | str | None = None

    # Metadata
    observed: datetime
    resulted: datetime
    entered_by: str | None = None

    # Location
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")
    location_uid: str | None = Field(None, alias="locationUid")
    location_name: str | None = Field(None, alias="locationName")

    # Interpretation
    interpretation_code: str | None = Field(None, alias="interpretationCode")
    interpretation_name: str | None = Field(None, alias="interpretationName")

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("observed", "resulted", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        return parse_datetime(v)

    @field_serializer("observed", "resulted")
    def serialize_datetime_fields(self, value: datetime | None) -> str | None:
        return format_datetime_for_mcp_response(value)

    @field_validator("result", mode="before")
    @classmethod
    def ensure_string_result(cls, v):
        """Ensure result is string"""
        return str(v) if v is not None else ""

    def model_post_init(self, __context: Any) -> None:
        """Post-init processing"""
        super().model_post_init(__context)

        # Parse blood pressure if applicable
        if self.type_name == "BLOOD PRESSURE" and "/" in self.result:
            self.systolic, self.diastolic = parse_blood_pressure(self.result)

    @property
    def is_abnormal(self) -> bool:
        """Check if vital sign is abnormal"""
        if not self.interpretation_code:
            return False
        interp = InterpretationCode.from_hl7(self.interpretation_code)
        return interp is not None and interp != InterpretationCode.NORMAL

    @property
    def is_critical(self) -> bool:
        """Check if vital sign is critical"""
        if not self.interpretation_code:
            return False
        interp = InterpretationCode.from_hl7(self.interpretation_code)
        return interp in [
            InterpretationCode.CRITICAL_HIGH,
            InterpretationCode.CRITICAL_LOW,
        ]

    @property
    def display_value(self) -> str:
        """Get display-friendly value with units"""
        result_str = self.result or "N/A"
        if self.units:
            return f"{result_str} {self.units}"
        return result_str

    @property
    def interpretation(self) -> InterpretationCode | None:
        """Get parsed interpretation code"""
        if not self.interpretation_code:
            return None
        return InterpretationCode.from_hl7(self.interpretation_code)

    @property
    def vital_type(self) -> VitalType | None:
        """Get vital type enum from type name"""
        type_mapping = {
            "BLOOD PRESSURE": VitalType.BP,
            "TEMPERATURE": VitalType.TEMP,
            "PULSE": VitalType.PULSE,
            "RESPIRATION": VitalType.RESP,
            "WEIGHT": VitalType.WEIGHT,
            "HEIGHT": VitalType.HEIGHT,
            "PAIN": VitalType.PAIN,
            "PULSE OXIMETRY": VitalType.O2_SAT,
        }
        return type_mapping.get(self.type_name.upper())


class LabResult(BasePatientModel):
    """Laboratory test result"""

    uid: str
    local_id: str = Field(alias="localId")

    # Test information
    type_code: str = Field(alias="typeCode")  # LOINC code
    type_name: str = Field(alias="typeName")  # "GLUCOSE"
    display_name: str | None = Field(None, alias="displayName")

    # Results - handle mixed types
    result: str | None = None  # Original value
    units: str | None = None

    # Reference ranges
    high: float | str | None = None
    low: float | str | None = None

    # Interpretation
    interpretation_code: str | None = Field(None, alias="interpretationCode")
    interpretation_name: str | None = Field(None, alias="interpretationName")

    # Grouping
    group_name: str | None = Field(None, alias="groupName")  # "CH 0527 3"
    group_uid: str | None = Field(None, alias="groupUid")

    # Metadata
    observed: datetime
    resulted: datetime
    verified: datetime | None = None

    # Order info
    order_uid: str | None = Field(None, alias="orderUid")
    lab_order_id: str | None = Field(None, alias="labOrderId")

    # Location
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")

    # Sample info
    specimen: str | None = None
    sample: str | None = None

    # Status
    status_code: str = Field(alias="statusCode")
    status_name: str = Field(alias="statusName")

    # Additional info
    comment: str | None = None

    @field_validator("local_id", "facility_code", "lab_order_id", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else v

    @field_validator("observed", "resulted", "verified", mode="before")
    @classmethod
    def parse_required_datetime(cls, v):
        """Parse required datetime fields"""
        return parse_datetime(v)

    @field_serializer("observed", "resulted", "verified")
    def serialize_datetime_fields(self, value: datetime) -> str:
        """Serialize required datetime fields to ISO format"""
        return format_datetime_with_default(value)

    @field_validator("result", mode="before")
    @classmethod
    def ensure_string_result(cls, v):
        """Ensure result is string"""
        return str(v) if v is not None else ""

    @property
    def is_abnormal(self) -> bool:
        """Check if lab result is abnormal"""
        return self.interpretation_code is not None

    @property
    def is_critical(self) -> bool:
        """Check if result is critically high or low"""
        if not self.interpretation_name:
            return False
        return "critical" in self.interpretation_name.lower()

    @property
    def interpretation(self) -> InterpretationCode | None:
        """Get interpretation as enum"""
        return InterpretationCode.from_hl7(self.interpretation_code)

    @property
    def display_value(self) -> str:
        """Get display-friendly value with units"""
        result_str = self.result or "N/A"
        if self.units:
            return f"{result_str} {self.units}"
        return result_str


class Consult(BasePatientModel):
    """Consultation record"""

    uid: str
    local_id: str = Field(alias="localId")

    # Consult details
    service: str  # "CARDIOLOGY"
    type_name: str = Field(alias="typeName")  # "CARDIOLOGY Cons"
    order_name: str = Field(alias="orderName")  # "CARDIOLOGY"
    order_uid: str = Field(alias="orderUid")

    # Status
    status_name: str = Field(alias="statusName")  # "PENDING", "SCHEDULED", etc.
    urgency: str = "Routine"  # "Routine", "Urgent", "STAT"

    # Dates
    date_time: datetime = Field(alias="dateTime")  # Order date
    scheduled_date: datetime | None = None
    completed_date: datetime | None = None

    # Provider info
    provider_uid: str | None = Field(None, alias="providerUid")
    provider_name: str | None = Field(None, alias="providerName")
    requesting_provider: str | None = None

    # Clinical info
    reason: str | None = None
    provisional_dx: ProvisionalDx | None = Field(None, alias="provisionalDx")

    # Location
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")

    # Type
    consult_procedure: str = Field(default="Consult", alias="consultProcedure")
    category: str = "C"

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("date_time", "scheduled_date", "completed_date", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        return parse_datetime(v)

    @field_serializer("date_time", "scheduled_date", "completed_date")
    def serialize_datetime_fields(self, value: datetime | None) -> str | None:
        """Serialize datetime fields to ISO format for JSON schema compliance"""
        return format_datetime_for_mcp_response(value)

    @property
    def is_active(self) -> bool:
        """Check if consult is active"""
        active_statuses = ["PENDING", "SCHEDULED", "ACTIVE"]
        return self.status_name.upper() in active_statuses

    @property
    def is_overdue(self) -> bool:
        """Check if consult is overdue (simple heuristic)"""
        if not self.is_active:
            return False
        # Consider overdue if more than 30 days old
        return (datetime.now(UTC) - self.date_time).days > 30

    @property
    def status(self) -> ConsultStatus:
        """Get status as enum"""
        return ConsultStatus.from_name(self.status_name)

    @property
    def urgency_level(self) -> Urgency:
        """Get urgency as enum"""
        return Urgency.from_name(self.urgency)
