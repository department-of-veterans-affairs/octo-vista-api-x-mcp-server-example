"""Patient data collection model"""

from datetime import datetime, timezone
from typing import Any

from pydantic import Field

from .base import BasePatientModel
from .clinical import Consult, LabResult, Medication, VitalSign
from .demographics import PatientDemographics


class PatientDataCollection(BasePatientModel):
    """
    Organized collection of patient data parsed from VPR JSON.
    This is the main model that gets cached.
    """

    # Core demographics - always present
    demographics: PatientDemographics

    # Clinical data arrays - may be empty
    vital_signs: list[VitalSign] = Field(default_factory=list)
    lab_results: list[LabResult] = Field(default_factory=list)
    consults: list[Consult] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)

    # Future expansion (stubs for now)
    # problems: List[Problem] = Field(default_factory=list)
    # allergies: List[Allergy] = Field(default_factory=list)
    # immunizations: List[Immunization] = Field(default_factory=list)
    # documents: List[Document] = Field(default_factory=list)
    # appointments: List[Appointment] = Field(default_factory=list)

    # Metadata
    source_station: str
    source_dfn: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cache_version: str = Field(default="1.0")
    total_items: int = 0

    # Store raw data for debugging (excluded from serialization)
    raw_data: dict[str, Any] | None = Field(default=None, exclude=True)

    @property
    def patient_name(self) -> str:
        """Convenience property for patient name"""
        return self.demographics.full_name

    @property
    def patient_dfn(self) -> str:
        """Convenience property for patient DFN"""
        return self.demographics.dfn or self.source_dfn

    @property
    def has_clinical_data(self) -> bool:
        """Check if any clinical data is present"""
        return bool(self.vital_signs or self.lab_results or self.consults)

    def get_latest_vitals(self) -> dict[str, VitalSign]:
        """Get most recent vital sign of each type"""
        latest: dict[str, VitalSign] = {}
        for vital in self.vital_signs:
            type_name = vital.type_name
            if type_name not in latest or vital.observed > latest[type_name].observed:
                latest[type_name] = vital
        return latest

    def get_abnormal_labs(self) -> list[LabResult]:
        """Get all abnormal lab results"""
        return [lab for lab in self.lab_results if lab.is_abnormal]

    def get_critical_labs(self) -> list[LabResult]:
        """Get critical lab results"""
        return [lab for lab in self.lab_results if lab.is_critical]

    def get_active_consults(self) -> list[Consult]:
        """Get active consultation records"""
        return [consult for consult in self.consults if consult.is_active]

    def get_overdue_consults(self) -> list[Consult]:
        """Get overdue consultation records"""
        return [consult for consult in self.consults if consult.is_overdue]

    def to_summary(self) -> dict[str, Any]:
        """
        Generate a summary view of patient data.
        Useful for quick overview displays.
        """
        latest_vitals = self.get_latest_vitals()

        summary: dict[str, Any] = {
            "patient": {
                "name": self.patient_name,
                "dfn": self.patient_dfn,
                "age": self.demographics.calculate_age(),
                "gender": self.demographics.gender_name,
                "ssn": self.demographics.ssn,
                "phone": self.demographics.primary_phone,
            },
            "vitals_summary": {
                "latest_count": len(latest_vitals),
                "has_abnormal": any(v.is_abnormal for v in latest_vitals.values()),
            },
            "labs_summary": {
                "total_count": len(self.lab_results),
                "abnormal_count": len(self.get_abnormal_labs()),
                "critical_count": len(self.get_critical_labs()),
            },
            "consults_summary": {
                "total_count": len(self.consults),
                "active_count": len(self.get_active_consults()),
                "overdue_count": len(self.get_overdue_consults()),
            },
            "data_freshness": {
                "retrieved_at": self.retrieved_at.isoformat(),
                "age_minutes": int(
                    (datetime.now(timezone.utc) - self.retrieved_at).total_seconds()
                    / 60
                ),
            },
        }

        # Add latest vital values
        if latest_vitals:
            summary["latest_vitals"] = {}
            for type_name, vital in latest_vitals.items():
                summary["latest_vitals"][type_name] = {
                    "value": vital.display_value,
                    "date": vital.observed.strftime("%Y-%m-%d %H:%M"),
                    "abnormal": vital.is_abnormal,
                }

        return summary
