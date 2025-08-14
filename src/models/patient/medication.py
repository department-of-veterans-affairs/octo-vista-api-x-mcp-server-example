"""Medication data models for patient records"""

from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import Field, field_serializer, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...services.parsers.patient.value_parser import (
    extract_frequency_from_sig,
    extract_route,
    normalize_medication_frequency,
)
from ...utils import get_logger
from ..utils import format_datetime_for_mcp_response
from .base import BasePatientModel

logger = get_logger()


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
    start_date: datetime | None = Field(default=None, alias="overallStart")
    end_date: datetime | None = Field(default=None, alias="overallStop")
    last_filled: datetime | None = Field(default=None, alias="lastFilled")

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

    @field_serializer("start_date", "end_date", "last_filled")
    def serialize_datetime_fields(self, value: datetime | None) -> str | None:
        """Serialize datetime fields to ISO format for JSON schema compliance"""
        return format_datetime_for_mcp_response(value)

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
        return not (self.end_date and self.end_date < datetime.now(UTC))

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
        days_remaining = (refill_due - datetime.now(UTC)).days

        return max(0, days_remaining)

    @property
    def needs_refill_soon(self) -> bool:
        """Check if medication needs refill within 7 days"""
        days_left = self.days_until_refill_needed
        return days_left is not None and days_left <= 7
