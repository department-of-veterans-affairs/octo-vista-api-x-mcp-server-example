"""Health factor data models for patient records"""

from datetime import datetime

from pydantic import Field, field_serializer, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from ..utils import format_datetime_with_default
from .base import BasePatientModel

logger = get_logger()


class HealthFactor(BasePatientModel):
    """Patient health factor/risk factor from VPR JSON"""

    uid: str
    local_id: str = Field(alias="localId")

    # Factor identification
    factor_name: str = Field(alias="name")
    category: str = Field(alias="categoryName")
    category_uid: str | None = Field(None, alias="categoryUid")
    summary: str | None = None

    # Severity and status (computed from category/name)
    severity: str | None = None  # mild, moderate, severe
    status: str = "active"  # active, resolved, inactive

    # Dates and metadata
    recorded_date: datetime = Field(alias="entered")
    recorded_by: str | None = None

    # Encounter and location info
    encounter_name: str | None = Field(None, alias="encounterName")
    encounter_uid: str | None = Field(None, alias="encounterUid")
    location_name: str | None = Field(None, alias="locationName")
    location_uid: str | None = Field(None, alias="locationUid")

    # Facility information
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")

    # Additional info
    comments: str | None = Field(None, alias="comment")
    display: bool = Field(default=True)

    # Clinical context
    kind: str = Field(default="Health Factor")

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("recorded_date", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        return parse_datetime(v)

    @field_serializer("recorded_date")
    def serialize_datetime_fields(self, value: datetime) -> str:
        """Serialize datetime fields to ISO format for JSON schema compliance"""
        return format_datetime_with_default(value)

    @field_validator("factor_name", mode="before")
    @classmethod
    def ensure_string_factor_name(cls, v):
        """Ensure factor name is string"""
        return str(v) if v is not None else ""
