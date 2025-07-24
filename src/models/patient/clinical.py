"""Clinical data models for patient records"""

from datetime import datetime, timedelta
from typing import Any

from pydantic import Field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...services.parsers.patient.value_parser import (
    extract_frequency_from_sig,
    extract_route,
    normalize_medication_frequency,
    parse_blood_pressure,
    parse_numeric_result,
)
from .base import (
    BasePatientModel,
    CodedValue,
    ConsultStatus,
    InterpretationCode,
    Urgency,
    VitalType,
)


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
    numeric_result: float | None = None  # Parsed numeric
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
        """Parse datetime format"""
        if isinstance(v, datetime):
            return v
        return parse_datetime(v)

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

        # Parse numeric result
        if self.numeric_result is None:
            self.numeric_result = parse_numeric_result(self.result)

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
        if self.units:
            return f"{self.result} {self.units}"
        return self.result

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
    display_name: str = Field(alias="displayName")

    # Results - handle mixed types
    result: str  # Original value
    numeric_result: float | None = None
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
    lab_order_id: int | None = Field(None, alias="labOrderId")

    # Location
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")
    performing_lab: str | None = None

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
    def parse_datetime(cls, v):
        """Parse datetime format"""
        if v is None or isinstance(v, datetime):
            return v
        return parse_datetime(v)

    @field_validator("result", mode="before")
    @classmethod
    def ensure_string_result(cls, v):
        """Ensure result is string"""
        return str(v) if v is not None else ""

    def model_post_init(self, __context: Any) -> None:
        """Post-init processing"""
        super().model_post_init(__context)

        # Parse numeric result if not already set
        if self.numeric_result is None:
            self.numeric_result = parse_numeric_result(self.result)

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
        if self.units:
            return f"{self.result} {self.units}"
        return self.result


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
    provisional_dx: CodedValue | None = Field(None, alias="provisionalDx")

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
        """Parse datetime format"""
        if v is None or isinstance(v, datetime):
            return v
        return parse_datetime(v)

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
        return (datetime.now() - self.date_time).days > 30

    @property
    def status(self) -> ConsultStatus:
        """Get status as enum"""
        return ConsultStatus.from_name(self.status_name)

    @property
    def urgency_level(self) -> Urgency:
        """Get urgency as enum"""
        return Urgency.from_name(self.urgency)


class Medication(BasePatientModel):
    """Patient medication record from VPR JSON"""

    uid: str
    local_id: str = Field(alias="localId")

    # Medication identification
    medication_name: str = Field(alias="productFormName")  # "METFORMIN TAB"
    generic_name: str | None = Field(None, alias="genericName")  # "Metformin HCl"
    brand_name: str | None = Field(None, alias="brandName")  # "Glucophage"
    strength: str | None = None  # "500MG", "10MG/5ML"

    # Dosing information
    dosage: str = Field(alias="dosageForm")  # "TABLET", "CAPSULE", "LIQUID"
    sig: str = Field(default="")  # Dosing instructions
    frequency: str | None = None  # "BID", "QD", "Q8H"
    route: str | None = None  # "PO", "IV", "IM"

    # Dates
    start_date: datetime = Field(alias="overallStart")
    end_date: datetime | None = Field(None, alias="overallStop")
    last_filled: datetime | None = Field(None, alias="lastFilled")

    # Status and supply information
    status: str = Field(alias="vaStatus")  # "ACTIVE", "DISCONTINUED", "COMPLETED"
    quantity: str | None = None  # "90"
    days_supply: int | None = Field(None, alias="daysSupply")  # 90
    refills_remaining: int | None = Field(None, alias="fillsRemaining")  # 5

    # Provider and pharmacy info
    prescriber: str | None = Field(None, alias="orders[0].providerName")
    prescriber_uid: str | None = Field(None, alias="orders[0].providerUid")
    pharmacy: str | None = Field(None, alias="pharmacyId")

    # Location
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")

    # Clinical classification
    va_class: str | None = Field(None, alias="vaClass")  # Drug class
    therapeutic_class: str | None = None

    # Instructions and notes
    patient_instructions: str | None = Field(None, alias="patientInstructions")
    provider_instructions: str | None = Field(None, alias="providerInstructions")

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("start_date", "end_date", "last_filled", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        """Parse datetime format"""
        if v is None or isinstance(v, datetime):
            return v
        return parse_datetime(v)

    @field_validator("medication_name", mode="before")
    @classmethod
    def ensure_string_medication_name(cls, v):
        """Ensure medication name is string"""
        return str(v) if v is not None else ""

    @field_validator("sig", mode="before")
    @classmethod
    def parse_sig_instructions(cls, v):
        """Parse SIG instructions from various formats"""
        if not v:
            return ""
        if isinstance(v, list) and v:
            return " ".join(str(item) for item in v)
        return str(v)

    def model_post_init(self, __context: Any) -> None:
        """Post-init processing for derived fields"""
        super().model_post_init(__context)

        # Extract strength from medication name if not provided
        if not self.strength and self.medication_name:
            import re

            # Look for patterns like "500MG", "10MG/5ML", "0.25MG"
            strength_match = re.search(
                r"(\d+(?:\.\d+)?(?:MG|MCG|ML|GM|UNITS?)(?:/\d+(?:ML|TAB)?)?)",
                self.medication_name.upper(),
            )
            if strength_match:
                self.strength = strength_match.group(1)

        # Parse frequency from sig if not provided
        if not self.frequency and self.sig:
            self.frequency = self._extract_frequency_from_sig(self.sig)

        # Parse route from sig if not provided
        if not self.route and self.sig:
            self.route = self._extract_route_from_sig(self.sig)

    def _extract_frequency_from_sig(self, sig: str) -> str | None:
        """Extract frequency from SIG instructions using centralized patterns"""
        return extract_frequency_from_sig(sig)

    def _extract_route_from_sig(self, sig: str) -> str | None:
        """Extract route of administration from SIG using centralized mappings"""
        return extract_route(sig)

    @property
    def is_active(self) -> bool:
        """Check if medication is currently active"""
        if self.status.upper() != "ACTIVE":
            return False

        # Check if end date has passed
        return not (self.end_date and self.end_date < datetime.now())

    @property
    def is_discontinued(self) -> bool:
        """Check if medication is discontinued"""
        return self.status.upper() in ["DISCONTINUED", "STOPPED", "EXPIRED"]

    @property
    def display_name(self) -> str:
        """Get display-friendly medication name with strength"""
        name = self.medication_name
        if self.strength and self.strength not in name:
            name = f"{name} {self.strength}"
        return name

    @property
    def display_frequency(self) -> str:
        """Get human-readable frequency using centralized mappings"""
        if not self.frequency:
            return "as directed"

        # Use centralized frequency normalization
        return normalize_medication_frequency(self.frequency)

    @property
    def days_until_refill_needed(self) -> int | None:
        """Calculate days until refill is needed"""
        if not self.last_filled or not self.days_supply:
            return None

        refill_due = self.last_filled + timedelta(days=self.days_supply)
        days_remaining = (refill_due - datetime.now()).days

        return max(0, days_remaining)

    @property
    def needs_refill_soon(self) -> bool:
        """Check if medication needs refill within 7 days"""
        days_left = self.days_until_refill_needed
        return days_left is not None and days_left <= 7
