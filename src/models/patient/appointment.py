"""Appointment data models for patient records"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from .base import BasePatientModel, FacilityInfo


class AppointmentStatus(str, Enum):
    """Appointment status enumeration"""

    SCHEDULED = "scheduled"
    KEPT = "kept"
    INPATIENT = "inpatient"
    NO_ACTION_TAKEN = "no-action-taken"
    NO_SHOW = "no-show"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class AppointmentType(str, Enum):
    """Appointment type/category enumeration based on VistA data"""

    OUTPATIENT_VISIT = "Outpatient Visit"
    ADMISSION = "Admission"
    PHONE_CONTACT = "Phone Contact"
    LABORATORY = "Laboratory"
    MICROBIOLOGY = "Microbiology"
    IMAGING = "IMAGING [C]"
    MENTAL_HEALTH = "MENTAL HEALTH [C]"
    HEPATITIS_C = "HEPATITIS C"
    DEP_EVAL = "DEP EVAL [C]"
    LCS_CT_SCAN_FREQUENCY = "LCS CT SCAN FREQUENCY [C]"
    LUNG_CANCER_SCREENING = "LUNG CANCER SCREENING (LCS) [C]"
    REMINDER_FACTORS = "REMINDER FACTORS [C]"
    VA_COVID_19 = "VA-COVID-19 [C]"


class AppointmentProvider(BasePatientModel):
    """Provider information for appointments"""

    provider_name: str = Field(alias="providerName")
    provider_uid: str = Field(alias="providerUid")


class AppointmentStopCode(BasePatientModel):
    """Stop code information for appointments"""

    name: str = Field(alias="stopCodeName")
    uid: str = Field(alias="stopCodeUid")


class AppointmentNamedType(BasePatientModel):
    """Type information for appointments"""

    code: int = Field(alias="typeCode")
    name: str = Field(alias="typeName")


class AppointmentCategory(BasePatientModel):
    """Category information for appointments"""

    type: AppointmentType | str | None = Field(None, alias="categoryName")
    code: str | None = Field(None, alias="categoryCode")


class AppointmentPatientClass(BasePatientModel):
    """Patient classification information for appointments"""

    code: str | None = Field(None, alias="patientClassCode")
    name: str | None = Field(None, alias="patientClassName")


class Appointment(BasePatientModel):
    """Appointment record for patient visits"""

    uid: str
    local_id: str = Field(alias="localId")

    # Basic appointment info
    appointment_date: datetime = Field(alias="dateTime")
    category: AppointmentCategory | None = None
    status: AppointmentStatus = Field(alias="appointmentStatus")

    # Facility information
    facility: FacilityInfo

    # Location information
    location_name: str | None = Field(None, alias="locationName")
    location_uid: str | None = Field(None, alias="locationUid")

    # Patient classification
    patient_class: AppointmentPatientClass | None = None

    # Provider information
    providers: list[AppointmentProvider] = []

    # Service and stop code information
    service: str | None = None
    stop_code: AppointmentStopCode | None = None

    # Type information
    type: AppointmentNamedType | None = None

    # Summary
    summary: str | None = None

    @field_validator("appointment_date", mode="before")
    @classmethod
    def parse_appointment_date(cls, v):
        """Parse appointment date using Vista date parser"""
        if v is None:
            # For appointments with no dateTime, we'll raise a validation error
            # since appointment_date is required
            raise ValueError(
                "Appointment requires a valid dateTime field for scheduling. "
                "Expected format: ISO datetime string (e.g., '2024-01-15T09:00:00') or datetime object."
            )

        if isinstance(v, datetime):
            return v
        else:
            return parse_datetime(str(v))

    @field_validator("local_id", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("status", mode="before")
    @classmethod
    def normalize_appointment_status(cls, v):
        """Normalize Vista appointment status values to enum values"""
        if isinstance(v, str):
            # Map Vista status values to our enum values (handles compound statuses)
            status_mapping = {
                "KEPT": "kept",
                "SCHEDULED": "scheduled",
                "SCHEDULED/KEPT": "kept",  # Handle slash-separated compound status -> kept
                "SCHEDULED-KEPT": "kept",  # Handle hyphen-separated compound status -> kept
                "NO-SHOW": "no-show",
                "NO SHOW": "no-show",  # Handle space-separated
                "CANCELLED": "cancelled",
                "CANCELED": "cancelled",
                "COMPLETED": "completed",
                "INPATIENT": "inpatient",
                "NO-ACTION-TAKEN": "no-action-taken",
                "NO ACTION TAKEN": "no-action-taken",
            }

            # Normalize the input status
            upper_status = v.upper().strip()

            # Handle compound statuses with slash separator
            if "/" in upper_status:
                # Convert slash to hyphen for compound statuses
                upper_status = upper_status.replace("/", "-")

            # Handle compound statuses with space separator
            if " " in upper_status and upper_status not in status_mapping:
                # Convert space to hyphen for compound statuses
                upper_status = upper_status.replace(" ", "-")

            if upper_status in status_mapping:
                mapped_status = status_mapping[upper_status]
                # Return the actual enum value, not just the string
                return AppointmentStatus(mapped_status)

            # If no mapping found, try to use as-is (lowercased)
            normalized = v.lower().strip().replace("/", "-").replace(" ", "-")
            try:
                return AppointmentStatus(normalized)
            except ValueError:
                # If it's not a valid enum value, default to scheduled
                return AppointmentStatus.SCHEDULED

        return v

    @field_validator("providers", mode="before")
    @classmethod
    def process_providers_array(cls, v):
        """Process providers array from JSON"""
        if isinstance(v, list):
            # Return the raw data for now - we'll create AppointmentProvider objects in model_post_init
            return v
        return v

    @field_validator("facility", mode="before")
    @classmethod
    def create_facility(cls, v, info):
        """Create FacilityInfo from input data"""
        if isinstance(v, dict):
            return v
        # If facility is not provided directly, create from facilityCode and facilityName
        if hasattr(info, "data"):
            data = info.data
            if "facilityCode" in data and "facilityName" in data:
                return {
                    "code": data["facilityCode"],
                    "name": data["facilityName"],
                }
        return v

    @field_validator("category", mode="before")
    @classmethod
    def create_category(cls, v, info):
        """Create AppointmentCategory from input data"""
        if isinstance(v, dict):
            return v
        # If category is not provided directly, create from categoryName and categoryCode
        if hasattr(info, "data"):
            data = info.data
            if "categoryName" in data or "categoryCode" in data:
                return {
                    "categoryName": data.get("categoryName"),
                    "categoryCode": data.get("categoryCode"),
                }
        return None

    @field_validator("patient_class", mode="before")
    @classmethod
    def create_patient_class(cls, v, info):
        """Create AppointmentPatientClass from input data"""
        if isinstance(v, dict):
            return v
        # If patient_class is not provided directly, create from patientClassCode and patientClassName
        if hasattr(info, "data"):
            data = info.data
            if "patientClassCode" in data or "patientClassName" in data:
                return {
                    "patientClassCode": data.get("patientClassCode"),
                    "patientClassName": data.get("patientClassName"),
                }
        return None

    @field_validator("stop_code", mode="before")
    @classmethod
    def create_stop_code(cls, v, info):
        """Create AppointmentStopCode from input data"""
        if isinstance(v, dict):
            return v
        # If stop_code is not provided directly, create from stopCodeName and stopCodeUid
        if hasattr(info, "data"):
            data = info.data
            if "stopCodeName" in data and "stopCodeUid" in data:
                return {
                    "stopCodeName": data["stopCodeName"],
                    "stopCodeUid": data["stopCodeUid"],
                }
        return None

    @field_validator("type", mode="before")
    @classmethod
    def create_type(cls, v, info):
        """Create AppointmentNamedType from input data"""
        if isinstance(v, dict):
            return v
        # If type is not provided directly, create from typeCode and typeName
        if hasattr(info, "data"):
            data = info.data
            if "typeCode" in data and "typeName" in data:
                return {"typeCode": data["typeCode"], "typeName": data["typeName"]}
        return None

    def model_post_init(self, __context: Any) -> None:
        """Post-init processing for appointments"""
        super().model_post_init(__context)
