"""CPT Code data models for patient records"""

from datetime import datetime

from pydantic import Field, field_serializer, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from ..utils import format_datetime_for_mcp_response
from .base import BasePatientModel

logger = get_logger()


class CPTCode(BasePatientModel):
    """Patient CPT procedure code from VPR JSON"""

    uid: str
    local_id: str = Field(alias="localId")

    # CPT Code identification
    cpt_code: str = Field(alias="cptCode")
    name: str = Field(alias="name", default="")
    type: str | None = Field(alias="type", default=None)

    # Procedure details
    entered: datetime | None = None
    quantity: int = Field(default=1)

    # Associated visit/encounter
    encounter: str | None = Field(None, alias="encounterUid")
    encounter_name: str | None = Field(None, alias="encounterName")

    # Location information
    facility_code: str | int = Field(alias="facilityCode")
    facility_name: str = Field(alias="facilityName")
    location_name: str | None = Field(None, alias="locationName")
    location_uid: str | None = Field(None, alias="locationUid")

    @field_validator("local_id", "facility_code", mode="before")
    @classmethod
    def ensure_string_fields(cls, v):
        """Ensure these fields are strings"""
        return str(v) if v is not None else ""

    @field_validator("entered", mode="before")
    @classmethod
    def parse_datetime_field(cls, v):
        return parse_datetime(v)

    @field_serializer("entered")
    def serialize_datetime_fields(self, value: datetime | None) -> str | None:
        """Serialize datetime fields to ISO format for JSON schema compliance"""
        return format_datetime_for_mcp_response(value)

    @field_validator("cpt_code", mode="before")
    @classmethod
    def normalize_cpt_code(cls, v):
        """Extract CPT code from URN format"""
        if not v:
            return ""
        # Handle URN format: "urn:cpt:82950" -> "82950"
        if isinstance(v, str) and v.startswith("urn:cpt:"):
            return v.split(":")[-1]
        return str(v)

    @property
    def display_name(self) -> str:
        """Get display-friendly procedure name"""
        if self.name:
            return f"{self.cpt_code} - {self.name}"
        return self.cpt_code
