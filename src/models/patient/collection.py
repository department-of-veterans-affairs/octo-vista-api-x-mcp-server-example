"""Patient data collection model"""

from datetime import UTC, datetime
from typing import Any

from pydantic import Field

from .allergy import Allergy
from .appointment import Appointment
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
from .treatment import Treatment
from .visits import Visit


class PatientDataCollection(BasePatientModel):
    """
    Organized collection of patient data parsed from VPR JSON.
    This is the main model that gets cached.
    """

    # Core demographics - always present
    demographics: PatientDemographics

    # Clinical data - stored as dictionaries for O(1) lookups by ID
    vital_signs_dict: dict[str, VitalSign] = Field(default_factory=dict)
    lab_results_dict: dict[str, LabResult] = Field(default_factory=dict)
    consults_dict: dict[str, Consult] = Field(default_factory=dict)
    medications_dict: dict[str, Medication] = Field(default_factory=dict)
    visits_dict: dict[str, Visit] = Field(default_factory=dict)
    health_factors_dict: dict[str, HealthFactor] = Field(default_factory=dict)
    treatments_dict: dict[str, Treatment] = Field(default_factory=dict)
    diagnoses_dict: dict[str, Diagnosis] = Field(default_factory=dict)
    orders_dict: dict[str, Order] = Field(default_factory=dict)
    documents_dict: dict[str, Document] = Field(default_factory=dict)
    cpt_codes_dict: dict[str, CPTCode] = Field(default_factory=dict)
    allergies_dict: dict[str, Allergy] = Field(default_factory=dict)
    povs_dict: dict[str, PurposeOfVisit] = Field(default_factory=dict)
    problems_dict: dict[str, Problem] = Field(default_factory=dict)
    appointments_dict: dict[str, Appointment] = Field(default_factory=dict)

    # Future expansion (stubs for now)
    # immunizations: List[Immunization] = Field(default_factory=list)

    # Metadata
    source_station: str
    source_icn: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cache_version: str = Field(default="1.0")
    total_items: int = 0

    # Store raw data for debugging (excluded from serialization)
    raw_data: dict[str, Any] | None = Field(default=None, exclude=True)

    @property
    def all_items(self) -> dict[str, BasePatientModel]:
        """Get all items in the collection"""
        return {
            **self.vital_signs_dict,
            **self.lab_results_dict,
            **self.consults_dict,
            **self.medications_dict,
            **self.visits_dict,
            **self.health_factors_dict,
            **self.diagnoses_dict,
            **self.orders_dict,
            **self.documents_dict,
            **self.cpt_codes_dict,
            **self.allergies_dict,
            **self.povs_dict,
            **self.problems_dict,
        }

    @property
    def patient_name(self) -> str:
        """Convenience property for patient name"""
        return self.demographics.full_name

    @property
    def patient_icn(self) -> str:
        """Convenience property for patient ICN"""
        return self.demographics.icn or self.source_icn

    @property
    def vital_signs(self) -> list[VitalSign]:
        """Vital signs as a list (backed by vital_signs_dict)"""
        return list(self.vital_signs_dict.values())

    @property
    def lab_results(self) -> list[LabResult]:
        """Lab results as a list (backed by lab_results_dict)"""
        return list(self.lab_results_dict.values())

    @property
    def consults(self) -> list[Consult]:
        """Consults as a list (backed by consults_dict)"""
        return list(self.consults_dict.values())

    @property
    def medications(self) -> list[Medication]:
        """Medications as a list (backed by medications_dict)"""
        return list(self.medications_dict.values())

    @property
    def visits(self) -> list[Visit]:
        """Visits as a list (backed by visits_dict)"""
        return list(self.visits_dict.values())

    @property
    def health_factors(self) -> list[HealthFactor]:
        """Health factors as a list (backed by health_factors_dict)"""
        return list(self.health_factors_dict.values())

    @property
    def treatments(self) -> list[Treatment]:
        """Treatments as a list (backed by treatments_dict)"""
        return list(self.treatments_dict.values())

    @property
    def diagnoses(self) -> list[Diagnosis]:
        """Diagnoses as a list (backed by diagnoses_dict)"""
        return list(self.diagnoses_dict.values())

    @property
    def orders(self) -> list[Order]:
        """Orders as a list (backed by orders_dict)"""
        return list(self.orders_dict.values())

    @property
    def documents(self) -> list[Document]:
        """Documents as a list (backed by documents_dict)"""
        return list(self.documents_dict.values())

    @property
    def cpt_codes(self) -> list[CPTCode]:
        """CPT codes as a list (backed by cpt_codes_dict)"""
        return list(self.cpt_codes_dict.values())

    @property
    def allergies(self) -> list[Allergy]:
        """Allergies as a list (backed by allergies_dict)"""
        return list(self.allergies_dict.values())

    @property
    def povs(self) -> list[PurposeOfVisit]:
        """Purposes of visit as a list (backed by povs_dict)"""
        return list(self.povs_dict.values())

    @property
    def problems(self) -> list[Problem]:
        """Problems as a list (backed by problems_dict)"""
        return list(self.problems_dict.values())

    @property
    def appointments(self) -> list[Appointment]:
        """Appointments as a list (backed by appointments_dict)"""
        return list(self.appointments_dict.values())

    @property
    def has_clinical_data(self) -> bool:
        """Check if any clinical data is present"""
        return bool(
            self.vital_signs or self.lab_results or self.consults or self.visits
        )

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
        """Get active visit records based on VistA status"""
        return [
            visit
            for visit in self.visits
            if visit.status_code and visit.status_code.lower() == "active"
        ]

    def get_inpatient_visits(self) -> list[Visit]:
        """Get inpatient visit records based on VistA visit type"""
        return [
            visit
            for visit in self.visits
            if visit.visit_type and visit.visit_type.value == "inpatient"
        ]

    def get_emergency_visits(self) -> list[Visit]:
        """Get emergency visit records based on VistA visit type"""
        return [
            visit
            for visit in self.visits
            if visit.visit_type and visit.visit_type.value == "emergency"
        ]

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

    def to_summary(self) -> dict[str, Any]:
        """
        Generate a summary view of patient data.
        Useful for quick overview displays.
        """

        summary: dict[str, Any] = {
            "patient": {
                "name": self.patient_name,
                "icn": self.patient_icn,
                "age": self.demographics.calculate_age(),
                "gender": self.demographics.gender_name,
                "ssn": self.demographics.ssn,
                "phone": self.demographics.primary_phone,
            },
            "vitals_summary": {
                "has_abnormal": any(
                    v.is_abnormal for v in self.vital_signs_dict.values()
                ),
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
            },
            "data_freshness": {
                "retrieved_at": self.retrieved_at.isoformat(),
                "age_minutes": int(
                    (datetime.now(UTC) - self.retrieved_at).total_seconds() / 60
                ),
            },
        }

        return summary
