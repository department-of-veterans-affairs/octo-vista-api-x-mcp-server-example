"""Patient data collection model"""

from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from .allergy import Allergy
from .base import BasePatientModel
from .clinical import Consult, LabResult, VitalSign
from .cpt_code import CPTCode
from .demographics import PatientDemographics
from .diagnosis import Diagnosis
from .document import Document
from .health_factor import HealthFactor
from .medication import Medication
from .order import Order
from .pov import PurposeOfVisit
from .problem import Problem
from .visits import Visit


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
    visits: list[Visit] = Field(default_factory=list)
    health_factors: list[HealthFactor] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    orders: list[Order] = Field(default_factory=list)
    documents: list[Document] = Field(default_factory=list)
    cpt_codes: list[CPTCode] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)
    povs: list[PurposeOfVisit] = Field(default_factory=list)
    problems: list[Problem] = Field(default_factory=list)

    # Future expansion (stubs for now)
    # immunizations: List[Immunization] = Field(default_factory=list)
    # appointments: List[Appointment] = Field(default_factory=list)

    # Metadata
    source_station: str
    source_dfn: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
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
        return bool(
            self.vital_signs or self.lab_results or self.consults or self.visits
        )

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

    def get_active_orders(self) -> list[Order]:
        """Get active order records"""
        return [order for order in self.orders if order.is_active]

    def get_overdue_consults(self) -> list[Consult]:
        """Get overdue consultation records"""
        return [consult for consult in self.consults if consult.is_overdue]

    def get_active_visits(self) -> list[Visit]:
        """Get active visit records"""
        return [visit for visit in self.visits if visit.is_active]

    def get_inpatient_visits(self) -> list[Visit]:
        """Get inpatient visit records"""
        return [visit for visit in self.visits if visit.is_inpatient]

    def get_emergency_visits(self) -> list[Visit]:
        """Get emergency visit records"""
        return [visit for visit in self.visits if visit.is_emergency]

    def get_completed_documents(self) -> list[Document]:
        """Get completed document records"""
        return [doc for doc in self.documents if doc.is_completed]

    def get_recent_documents(self, days: int = 30) -> list[Document]:
        """Get documents from the last N days"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.now(UTC) - timedelta(days=days)
        return [
            doc
            for doc in self.documents
            if doc.reference_date_time is not None
            and doc.reference_date_time >= cutoff_date
        ]

    def get_progress_notes(self) -> list[Document]:
        """Get progress note documents"""
        return [doc for doc in self.documents if doc.is_progress_note]

    def get_consult_notes(self) -> list[Document]:
        """Get consult note documents"""
        return [doc for doc in self.documents if doc.is_consult_note]

    def get_surgical_procedures(self) -> list[CPTCode]:
        """Get surgical procedures from CPT codes"""
        return [cpt for cpt in self.cpt_codes if cpt.is_surgical]

    def get_diagnostic_procedures(self) -> list[CPTCode]:
        """Get diagnostic procedures from CPT codes"""
        return [cpt for cpt in self.cpt_codes if cpt.is_diagnostic]

    def get_procedures_by_encounter(self) -> dict[str, list[CPTCode]]:
        """Group procedures by encounter"""
        encounters: dict[str, list[CPTCode]] = {}
        for cpt in self.cpt_codes:
            encounter_key = cpt.associated_visit_uid or "no_encounter"
            if encounter_key not in encounters:
                encounters[encounter_key] = []
            encounters[encounter_key].append(cpt)
        return encounters

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
            "visits_summary": {
                "total_count": len(self.visits),
                "active_count": len(self.get_active_visits()),
                "inpatient_count": len(self.get_inpatient_visits()),
                "emergency_count": len(self.get_emergency_visits()),
            },
            "documents_summary": {
                "total_count": len(self.documents),
                "completed_count": len(self.get_completed_documents()),
                "progress_notes_count": len(self.get_progress_notes()),
                "consult_notes_count": len(self.get_consult_notes()),
            },
            "orders_summary": {
                "total_count": len(self.orders),
                "active_count": len(self.get_active_orders()),
            },
            "procedures_summary": {
                "total_count": len(self.cpt_codes),
                "surgical_count": len(self.get_surgical_procedures()),
                "diagnostic_count": len(self.get_diagnostic_procedures()),
                "encounters_count": len(self.get_procedures_by_encounter()),
            },
            "data_freshness": {
                "retrieved_at": self.retrieved_at.isoformat(),
                "age_minutes": int(
                    (datetime.now(UTC) - self.retrieved_at).total_seconds() / 60
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
