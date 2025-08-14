"""Diagnosis data models for patient records"""

from datetime import datetime

from pydantic import Field, field_serializer, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from ..utils import format_datetime_for_mcp_response
from .base import BasePatientModel

logger = get_logger()


class Diagnosis(BasePatientModel):
    """Patient diagnosis from VPR JSON"""

    uid: str
    local_id: str = Field(alias="localId")

    # ICD Code information
    icd_code: str = Field(alias="icdCode")
    icd_version: str = Field(default="ICD-10")  # ICD-9 or ICD-10
    description: str = Field(alias="icdName")

    # Diagnosis classification
    diagnosis_type: str = Field(
        default="secondary"
    )  # primary, secondary, admitting, discharge, rule-out
    status: str = Field(default="active")  # active, resolved, chronic, rule-out

    # Dates and provider info
    diagnosis_date: datetime | None = Field(default=None, alias="entered")
    provider: str | None = Field(default=None, alias="providerName")
    provider_uid: str | None = Field(default=None, alias="providerUid")

    # Associated visit/encounter
    associated_visit_uid: str | None = Field(default=None, alias="encounterUid")
    encounter_name: str | None = Field(None, alias="encounterName")

    # Facility information
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")

    # Additional context
    comments: str | None = Field(default=None, alias="comment")
    summary: str | None = None

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("diagnosis_date", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        """Parse datetime format"""
        if v is None or isinstance(v, datetime):
            return v
        return parse_datetime(v)

    @field_serializer("diagnosis_date")
    def serialize_datetime_fields(self, value: datetime | None) -> str | None:
        """Serialize datetime fields to ISO format for JSON schema compliance"""
        return format_datetime_for_mcp_response(value)

    @field_validator("icd_code", mode="before")
    @classmethod
    def ensure_string_icd_code(cls, v):
        """Ensure ICD code is string and clean"""
        if v is None:
            return ""
        return str(v).strip().upper()

    @field_validator("description", mode="before")
    @classmethod
    def ensure_string_description(cls, v):
        """Ensure description is string"""
        return str(v) if v is not None else ""

    @property
    def body_system(self) -> str:
        """Get body system classification for this diagnosis"""
        from ...services.validators.clinical_validators import (
            classify_diagnosis_body_system,
        )

        return classify_diagnosis_body_system(self.icd_code, self.description)

    @property
    def is_primary(self) -> bool:
        """Check if this is a primary diagnosis"""
        return self.diagnosis_type.lower() == "primary"

    @property
    def is_chronic(self) -> bool:
        """Check if this is a chronic condition"""
        from ...services.validators.clinical_validators import is_chronic_diagnosis

        return is_chronic_diagnosis(self.icd_code, self.description)

    @property
    def severity_level(self) -> str:
        """Get severity level for this diagnosis"""
        from ...services.validators.clinical_validators import assess_diagnosis_severity

        return assess_diagnosis_severity(
            self.icd_code, self.description, self.diagnosis_type
        )

    @property
    def is_valid_icd(self) -> bool:
        """Validate ICD code format"""
        from ...services.validators.clinical_validators import validate_icd_code

        return validate_icd_code(self.icd_code, self.icd_version)
