"""Vista clinical models"""

from pydantic import Field, field_validator

from ..base import BaseVistaModel


class Medication(BaseVistaModel):
    """Medication information"""

    id: str | None = None
    name: str = Field(..., description="Medication name and strength")
    sig: str = Field(..., description="Dosing instructions")
    start_date: str | None = None
    stop_date: str | None = None
    status: str = Field(default="ACTIVE")
    quantity: str | None = None
    refills: int | None = None
    prescriber: str | None = None
    pharmacy: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Ensure status is uppercase"""
        return v.upper() if v else "ACTIVE"


class LabResult(BaseVistaModel):
    """Laboratory result"""

    id: str | None = None
    test_name: str
    value: str
    units: str | None = None
    reference_range: str | None = None
    flag: str | None = None
    status: str | None = None
    date_time: str
    ordering_provider: str | None = None

    @property
    def is_abnormal(self) -> bool:
        """Check if result is abnormal"""
        return bool(self.flag and self.flag in ["H", "L", "C", "A"])


class VitalSign(BaseVistaModel):
    """Vital sign measurement"""

    type: str = Field(..., description="Vital sign type (BP, P, R, T, WT, HT)")
    value: str
    units: str | None = None
    date_time: str
    qualifiers: str | None = None
    entered_by: str | None = None

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
    icd_code: str | None = None
    snomed_code: str | None = None
    description: str
    status: str = Field(default="ACTIVE")
    onset_date: str | None = None
    resolved_date: str | None = None
    type: str | None = None  # ACUTE/CHRONIC
    service_connected: bool = False
    priority: str | None = None


class Allergy(BaseVistaModel):
    """Allergy/adverse reaction"""

    id: str | None = None
    agent: str = Field(..., description="Allergen name")
    type: str | None = None
    reactions: list[str] = Field(default_factory=list)
    severity: str | None = None
    date_entered: str | None = None
    entered_by: str | None = None
    verified: bool = False
    comments: str | None = None
