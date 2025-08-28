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
    def patient_dfn(self) -> str:
        """Convenience property for patient DFN"""
        return self.demographics.dfn or self.source_dfn

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

    def get_procedures_by_encounter(self) -> dict[str, list[CPTCode]]:
        """Group procedures by encounter"""
        encounters: dict[str, list[CPTCode]] = {}
        for cpt in self.cpt_codes:
            encounter_key = cpt.encounter or "no_encounter"
            if encounter_key not in encounters:
                encounters[encounter_key] = []
            encounters[encounter_key].append(cpt)
        return encounters

    def get_active_treatments(self) -> list[Treatment]:
        """Get active treatment records"""
        return [treatment for treatment in self.treatments if treatment.is_active]

    def get_completed_treatments(self) -> list[Treatment]:
        """Get completed treatment records"""
        return [treatment for treatment in self.treatments if treatment.is_completed]

    def get_scheduled_treatments(self) -> list[Treatment]:
        """Get scheduled treatment records"""
        return [treatment for treatment in self.treatments if treatment.is_scheduled]

    def get_related_order_for_treatment(self, treatment: Treatment) -> Order | None:
        """Get the order that initiated a treatment"""
        if not treatment.related_order_uid:
            return None

        for order in self.orders:
            if order.uid == treatment.related_order_uid:
                return order
        return None

    def get_treatments_for_order(self, order: Order) -> list[Treatment]:
        """Get all treatments that resulted from a specific order"""
        treatments = [
            treatment
            for treatment in self.treatments
            if treatment.related_order_uid == order.uid
        ]
        return treatments

    def get_encounter_context_for_treatment(
        self, treatment: Treatment
    ) -> dict[str, Any]:
        """Get encounter/visit context for a treatment based on date proximity and related orders"""
        context: dict[str, Any] = {
            "related_order": None,
            "concurrent_procedures": [],
            "encounter_uid": None,
            "encounter_name": None,
            "visit_date": None,
        }

        # First, try to get related order
        related_order = self.get_related_order_for_treatment(treatment)
        if related_order:
            context["related_order"] = {
                "uid": related_order.uid,
                "name": related_order.name,
                "content": related_order.content,
                "service": related_order.service,
                "status": related_order.status,
                "provider": related_order.provider_name,
                "entered": (
                    related_order.entered.isoformat() if related_order.entered else None
                ),
            }

        # Find concurrent procedures on the same date (potential encounter indicators)
        treatment_date = treatment.date.date()
        concurrent_procedures = []
        encounter_uid = None
        encounter_name = None

        for cpt in self.cpt_codes:
            if cpt.entered and cpt.entered.date() == treatment_date:
                concurrent_procedures.append(
                    {
                        "cpt_code": cpt.cpt_code,
                        "description": cpt.name,
                        "location": cpt.location_name,
                    }
                )

                # Use encounter info from the first matching procedure
                if not encounter_uid and cpt.encounter:
                    encounter_uid = cpt.encounter
                    encounter_name = cpt.encounter_name

        context["concurrent_procedures"] = concurrent_procedures
        context["encounter_uid"] = encounter_uid
        context["encounter_name"] = encounter_name
        context["visit_date"] = treatment_date.isoformat() if treatment_date else None

        return context

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
