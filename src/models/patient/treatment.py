"""Treatment models for patient records"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import Field, field_validator

from ...services.parsers.patient.datetime_parser import parse_datetime
from ...utils import get_logger
from .base import BasePatientModel

if TYPE_CHECKING:
    pass

logger = get_logger()


class TreatmentStatusInput(str, Enum):
    """Valid input values for treatment status"""

    COMPLETED = "COMPLETED"
    COMPLETE = "COMPLETE"  # Alternative from VistA
    IN_PROGRESS = "IN_PROGRESS"
    ACTIVE = "ACTIVE"  # Maps to IN_PROGRESS
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    DISCONTINUED = "DISCONTINUED"
    DISCONTINUED_EDIT = "DISCONTINUED/EDIT"
    EXPIRED = "EXPIRED"
    LAPSED = "LAPSED"


class TreatmentStatusFilter(str, Enum):
    """Valid filter values for treatment status"""

    ACTIVE = "active"
    COMPLETED = "completed"
    PLANNED = "planned"


class TreatmentStatus(str, Enum):
    """Treatment status values"""

    COMPLETED = "completed"
    IN_PROGRESS = "in-progress"
    PENDING = "pending"
    SCHEDULED = "scheduled"
    DISCONTINUED = "discontinued"
    EXPIRED = "expired"
    LAPSED = "lapsed"
    EDITED_DISCONTINUED = "edited-discontinued"

    @classmethod
    def from_external_value(cls, value: str | None) -> TreatmentStatus:
        """Create from external status value with validation"""
        if not value:
            return cls.PENDING

        # Normalize the input value
        normalized = value.upper().strip()

        # Direct string mapping for efficiency
        match normalized:
            case "COMPLETED" | "COMPLETE":
                return cls.COMPLETED
            case "IN_PROGRESS" | "IN-PROGRESS" | "ACTIVE":
                return cls.IN_PROGRESS
            case "PENDING":
                return cls.PENDING
            case "SCHEDULED":
                return cls.SCHEDULED
            case "DISCONTINUED":
                return cls.DISCONTINUED
            case "DISCONTINUED/EDIT":
                return cls.EDITED_DISCONTINUED
            case "EXPIRED":
                return cls.EXPIRED
            case "LAPSED":
                return cls.LAPSED
            case _:
                # Fallback for unknown values
                return cls.PENDING

    @classmethod
    def is_active(cls, status: str) -> bool:
        """Check if status indicates active treatment"""
        return status in [cls.IN_PROGRESS]

    @classmethod
    def is_completed(cls, status: str) -> bool:
        """Check if status indicates completed treatment"""
        return status == cls.COMPLETED

    @classmethod
    def is_pending(cls, status: str) -> bool:
        """Check if status indicates pending treatment"""
        return status == cls.PENDING

    @classmethod
    def is_scheduled(cls, status: str) -> bool:
        """Check if status indicates scheduled treatment"""
        return status == cls.SCHEDULED

    @classmethod
    def is_discontinued(cls, status: str) -> bool:
        """Check if status indicates discontinued treatment"""
        return status in [cls.DISCONTINUED, cls.EDITED_DISCONTINUED]

    @classmethod
    def is_expired(cls, status: str) -> bool:
        """Check if status indicates expired treatment"""
        return status == cls.EXPIRED

    @classmethod
    def is_lapsed(cls, status: str) -> bool:
        """Check if status indicates lapsed treatment"""
        return status == cls.LAPSED


class Treatment(BasePatientModel):
    """Treatment record model"""

    # Core identifiers
    uid: str = Field(..., description="Unique treatment identifier")

    # Treatment details
    name: str = Field(..., description="Treatment name")
    treatment_type: str | None = Field(None, description="Type of treatment")
    category: str | None = Field(None, description="Treatment category")

    # Dates and timing
    date: datetime = Field(..., description="Treatment date")
    entered: datetime | None = Field(None, description="Date treatment was entered")

    # Status and progress
    status: TreatmentStatus = Field(
        default=TreatmentStatus.PENDING, description="Treatment status"
    )
    outcome: str | None = Field(None, description="Treatment outcome")

    # Provider and location
    provider_name: str | None = Field(None, description="Provider name")
    provider_uid: str | None = Field(None, description="Provider UID")
    location_name: str | None = Field(None, description="Location name")
    location_uid: str | None = Field(None, description="Location UID")

    # Related records
    related_order_uid: str | None = Field(None, description="Related order UID")
    related_visit_uid: str | None = Field(None, description="Related visit UID")

    # Additional metadata
    facility_code: str | None = Field(None, description="Facility code")
    facility_name: str | None = Field(None, description="Facility name")

    @field_validator("date", "entered", mode="before")
    @classmethod
    def parse_dates(cls, v):
        """Parse VistA date strings"""
        return parse_datetime(v)

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v):
        """Parse treatment status"""
        if isinstance(v, TreatmentStatus):
            return v
        return TreatmentStatus.from_external_value(str(v))

    @property
    def is_active(self) -> bool:
        """Check if treatment is currently active"""
        return TreatmentStatus.is_active(self.status)

    @property
    def is_completed(self) -> bool:
        """Check if treatment is completed"""
        return TreatmentStatus.is_completed(self.status)

    @property
    def is_pending(self) -> bool:
        """Check if treatment is pending"""
        return TreatmentStatus.is_pending(self.status)

    @property
    def is_scheduled(self) -> bool:
        """Check if treatment is scheduled"""
        return TreatmentStatus.is_scheduled(self.status)

    @property
    def is_discontinued(self) -> bool:
        """Check if treatment is discontinued"""
        return TreatmentStatus.is_discontinued(self.status)

    @property
    def is_expired(self) -> bool:
        """Check if treatment is expired"""
        return TreatmentStatus.is_expired(self.status)

    @property
    def is_lapsed(self) -> bool:
        """Check if treatment is lapsed"""
        return TreatmentStatus.is_lapsed(self.status)

    @property
    def has_outcome(self) -> bool:
        """Check if treatment has an outcome recorded"""
        return bool(self.outcome and self.outcome.strip())

    @property
    def display_name(self) -> str:
        """Get display name for treatment"""
        if self.treatment_type and self.treatment_type != self.name:
            return f"{self.treatment_type}: {self.name}"
        return self.name

    @property
    def provider_display(self) -> str:
        """Get provider display name"""
        return self.provider_name or "Unknown Provider"

    @property
    def location_display(self) -> str:
        """Get location display name"""
        return self.location_name or "Unknown Location"

    def to_summary(self) -> dict:
        """Convert to summary format"""
        return {
            "uid": self.uid,
            "name": self.name,
            "type": self.treatment_type,
            "date": self.date.isoformat(),
            "status": self.status,
            "provider": self.provider_display,
            "location": self.location_display,
            "has_outcome": self.has_outcome,
        }
