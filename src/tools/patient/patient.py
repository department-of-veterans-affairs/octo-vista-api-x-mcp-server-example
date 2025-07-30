"""Patient-related MCP tools using cached VPR data"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...models.responses import PatientSearchResponse
from ...services.data import get_patient_data
from ...services.formatters import (
    format_lab_type,
    format_service_name,
    format_status,
    format_urgency,
    format_vital_type,
)
from ...services.parsers.vista import parse_patient_search
from ...services.rpc import build_single_string_param, execute_rpc
from ...services.validators import validate_dfn
from ...utils import build_metadata, get_default_duz, get_default_station
from ...vista.base import BaseVistaClient

logger = logging.getLogger(__name__)


def register_patient_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register patient-related tools with the MCP server"""

    # TODO: This tool will be removed in the future as patient context is injected by CPRS.
    @mcp.tool()
    async def search_patients(
        search_term: str,
        station: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Search for patients across the Vista system using partial name or SSN matching

        Performs case-insensitive prefix search on patient names or exact match on SSN
        fragments. Useful for finding patients when full details aren't known.

        Args:
            search_term: Either:
                - Name prefix of 2+ characters (e.g., "SMI" finds Smith, Smithson)
                - Last 4 digits of SSN for exact matching
                - Full last name for broader results
            station: Vista station number for facility-specific search (default: user's home station)
            limit: Maximum results to return, range 1-100 (default: 10)

        Returns:
            List of matching patients with:
            - Full name, DOB, SSN (masked)
            - DFN (patient's unique identifier) for subsequent data retrieval
            - Age and gender
            - Station where patient record exists
            Results sorted by name alphabetically
        """
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Execute RPC with standardized error handling
        rpc_result = await execute_rpc(
            vista_client=vista_client,
            rpc_name="ORWPT LIST",
            parameters=build_single_string_param(f"^{search_term.upper()}"),
            parser=parse_patient_search,
            station=station,
            caller_duz=caller_duz,
            error_response_builder=lambda error, metadata: PatientSearchResponse.error_response(
                error=error,
                metadata=metadata,
            ).model_dump(),
        )

        # Check if this is an error response
        if "error" in rpc_result:
            return rpc_result

        # Get parsed data and metadata
        patients = rpc_result["parsed_data"]
        metadata = rpc_result["metadata"]

        # Add station to each patient
        for patient in patients:
            patient.station = station

        # Limit results
        if limit and len(patients) > limit:
            patients = patients[:limit]

        # Build response
        response = PatientSearchResponse(
            success=True,
            search_term=search_term,
            station=station,
            count=len(patients),
            patients=patients,
            metadata=metadata,
        )

        return response.model_dump()

    @mcp.tool()
    async def get_patient_vitals(
        patient_dfn: str,
        station: str | None = None,
        vital_type: str | None = None,
        days_back: int = 30,
    ) -> dict[str, Any]:
        """
        Retrieve recent vital sign measurements for a specific patient

        Fetches vital signs including blood pressure, temperature, pulse, respiration,
        weight, height, BMI, pain score, and oxygen saturation. Data is cached for
        performance and includes trend analysis.

        Args:
            patient_dfn: Patient's unique identifier (DFN) in the Vista system
            station: Vista station number for multi-site access (default: user's home station)
            vital_type: Filter by specific vital type (optional):
                - "BLOOD PRESSURE" - Systolic/diastolic readings
                - "TEMPERATURE" - Body temperature
                - "PULSE" - Heart rate
                - "RESPIRATION" - Breathing rate
                - "WEIGHT" - Patient weight
                - "HEIGHT" - Patient height
                - "PAIN" - Pain score (0-10)
                - "PULSE OXIMETRY" - Oxygen saturation
            days_back: Number of days of history to retrieve, range 1-365 (default: 30)

        Returns:
            Vital signs data including:
            - Latest reading for each vital type with timestamps
            - Historical readings for trend analysis
            - Abnormal/critical flags based on reference ranges
            - Measurement units and location where taken
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return {
                "success": False,
                "error": "Invalid patient DFN format. DFN must be numeric.",
                "metadata": build_metadata(station=station),
            }

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter vitals
            cutoff_date = datetime.now() - timedelta(days=days_back)
            vitals = [v for v in patient_data.vital_signs if v.observed >= cutoff_date]

            # Filter by type if specified
            if vital_type:
                vitals = [
                    v for v in vitals if v.type_name.upper() == vital_type.upper()
                ]

            # Get latest of each type
            latest_vitals = patient_data.get_latest_vitals()

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                    "age": patient_data.demographics.calculate_age(),
                },
                "vitals": {
                    "count": len(vitals),
                    "days_back": days_back,
                    "filtered_type": vital_type,
                    "latest": {
                        format_vital_type(type_name): {
                            "value": vital.display_value,
                            "date": vital.observed.isoformat(),
                            "abnormal": vital.is_abnormal,
                            "critical": vital.is_critical,
                        }
                        for type_name, vital in latest_vitals.items()
                    },
                    "history": [
                        {
                            "type": format_vital_type(v.type_name),
                            "value": v.display_value,
                            "date": v.observed.isoformat(),
                            "abnormal": v.is_abnormal,
                            "critical": v.is_critical,
                            "location": v.location_name,
                        }
                        for v in vitals
                    ],
                },
                "metadata": {
                    **build_metadata(
                        station=station,
                        duration_ms=int((time.time() - start_time) * 1000),
                    ),
                    "rpc": {
                        "rpc": "VPR GET PATIENT DATA JSON",
                        "context": "LHS RPC CONTEXT",
                        "jsonResult": True,
                        "parameters": [{"namedArray": {"patientId": patient_dfn}}],
                    },
                    "duz": caller_duz,
                },
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_vitals")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }

    @mcp.tool()
    async def get_patient_labs(
        patient_dfn: str,
        station: str | None = None,
        abnormal_only: bool = False,
        lab_type: str | None = None,
        days_back: int = 90,
    ) -> dict[str, Any]:
        """
        Retrieve laboratory test results and trends for a specific patient

        Fetches comprehensive lab results including chemistry panels, hematology,
        microbiology, and specialized tests. Results include reference ranges,
        abnormal flags, and historical trends for monitoring changes over time.

        Args:
            patient_dfn: Patient's unique identifier (DFN) in the Vista system
            station: Vista station number for multi-site access (default: user's home station)
            abnormal_only: Return only abnormal/critical results when True (default: False)
            lab_type: Filter by specific test name (optional), examples:
                - "GLUCOSE" - Blood sugar levels
                - "HEMOGLOBIN" - Red blood cell count
                - "CREATININE" - Kidney function
                - "TSH" - Thyroid function
                - "CHOLESTEROL" - Lipid panel
            days_back: Number of days of history to retrieve, range 1-730 (default: 90)

        Returns:
            Laboratory data including:
            - Grouped results by test type with latest values
            - Historical trends for each test (up to 5 most recent)
            - Abnormal/critical flags with reference ranges
            - Test metadata (specimen type, collection date, verified date)
            - Interpretation codes when available
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return {
                "success": False,
                "error": "Invalid patient DFN format. DFN must be numeric.",
                "metadata": build_metadata(station=station),
            }

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter labs
            cutoff_date = datetime.now() - timedelta(days=days_back)
            labs = [
                lab for lab in patient_data.lab_results if lab.observed >= cutoff_date
            ]

            # Filter by abnormal status
            if abnormal_only:
                labs = [lab for lab in labs if lab.is_abnormal]

            # Filter by type
            if lab_type:
                labs = [
                    lab for lab in labs if lab_type.upper() in lab.type_name.upper()
                ]

            # Group by test type
            lab_groups: dict[str, list[Any]] = {}
            for lab in labs:
                if lab.type_name not in lab_groups:
                    lab_groups[lab.type_name] = []
                lab_groups[lab.type_name].append(lab)

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                    "age": patient_data.demographics.calculate_age(),
                },
                "labs": {
                    "count": len(labs),
                    "abnormal_count": len([lab for lab in labs if lab.is_abnormal]),
                    "critical_count": len([lab for lab in labs if lab.is_critical]),
                    "days_back": days_back,
                    "filters": {
                        "abnormal_only": abnormal_only,
                        "lab_type": lab_type,
                    },
                    "by_type": {
                        format_lab_type(test_type): {
                            "count": len(results),
                            "latest": {
                                "value": results[0].display_value,
                                "date": results[0].observed.isoformat(),
                                "abnormal": results[0].is_abnormal,
                                "critical": results[0].is_critical,
                                "reference_range": (
                                    f"{results[0].low} - {results[0].high}"
                                    if results[0].low and results[0].high
                                    else None
                                ),
                            },
                            "trend": [
                                {
                                    "value": r.result,
                                    "numeric": r.numeric_result,
                                    "date": r.observed.isoformat(),
                                    "abnormal": r.is_abnormal,
                                }
                                for r in results[:5]  # Last 5 results
                            ],
                        }
                        for test_type, results in lab_groups.items()
                    },
                    "all_results": [
                        {
                            "test": lab.type_name,
                            "value": lab.display_value,
                            "date": lab.observed.isoformat(),
                            "abnormal": lab.is_abnormal,
                            "critical": lab.is_critical,
                            "interpretation": lab.interpretation_name,
                            "specimen": lab.specimen,
                            "group": lab.group_name,
                        }
                        for lab in labs[:100]  # Limit to 100 results
                    ],
                },
                "metadata": {
                    **build_metadata(
                        station=station,
                        duration_ms=int((time.time() - start_time) * 1000),
                    ),
                    "rpc": {
                        "rpc": "VPR GET PATIENT DATA JSON",
                        "context": "LHS RPC CONTEXT",
                        "jsonResult": True,
                        "parameters": [{"namedArray": {"patientId": patient_dfn}}],
                    },
                    "duz": caller_duz,
                },
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_labs")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }

    @mcp.tool()
    async def get_patient_consults(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """
        Retrieve consultation requests and referrals for a specific patient

        Tracks inter-specialty consultations including cardiology, neurology,
        mental health, and other specialties. Monitors consultation lifecycle
        from request through completion, helping identify delays in care.

        Args:
            patient_dfn: Patient's unique identifier (DFN) in the Vista system
            station: Vista station number for multi-site access (default: user's home station)
            active_only: When True, returns only pending/active consultations;
                        when False, includes completed and cancelled (default: True)

        Returns:
            Consultation data including:
            - Summary counts (total, active, overdue)
            - Overdue consultations with days elapsed
            - Detailed list with service, urgency, status, and dates
            - Requesting and consulting provider information
            - Reason for consultation and provisional diagnosis
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return {
                "success": False,
                "error": "Invalid patient DFN format. DFN must be numeric.",
                "metadata": build_metadata(station=station),
            }

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter consults
            consults = patient_data.consults
            if active_only:
                consults = [c for c in consults if c.is_active]

            # Get overdue consults
            overdue_consults = [c for c in consults if c.is_overdue]

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                },
                "consults": {
                    "total": len(patient_data.consults),
                    "active": len([c for c in patient_data.consults if c.is_active]),
                    "overdue": len(overdue_consults),
                    "filters": {
                        "active_only": active_only,
                    },
                    "overdue_list": [
                        {
                            "service": format_service_name(c.service),
                            "urgency": format_urgency(c.urgency),
                            "ordered": c.date_time.isoformat(),
                            "days_overdue": (datetime.now() - c.date_time).days,
                            "reason": c.reason,
                        }
                        for c in overdue_consults
                    ],
                    "all_consults": [
                        {
                            "id": c.local_id,
                            "service": format_service_name(c.service),
                            "status": format_status(c.status_name),
                            "urgency": format_urgency(c.urgency),
                            "ordered": c.date_time.isoformat(),
                            "scheduled": (
                                c.scheduled_date.isoformat()
                                if c.scheduled_date
                                else None
                            ),
                            "completed": (
                                c.completed_date.isoformat()
                                if c.completed_date
                                else None
                            ),
                            "provider": c.provider_name,
                            "reason": c.reason,
                            "overdue": c.is_overdue,
                        }
                        for c in consults
                    ],
                },
                "metadata": {
                    **build_metadata(
                        station=station,
                        duration_ms=int((time.time() - start_time) * 1000),
                    ),
                    "rpc": {
                        "rpc": "VPR GET PATIENT DATA JSON",
                        "context": "LHS RPC CONTEXT",
                        "jsonResult": True,
                        "parameters": [{"namedArray": {"patientId": patient_dfn}}],
                    },
                    "duz": caller_duz,
                },
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_consults")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }

    @mcp.tool()
    async def get_patient_medications(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
        therapeutic_class: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Retrieve current and historical medications for a specific patient

        Provides comprehensive medication list including dosing instructions,
        refill status, and potential drug interactions. Critical for medication
        reconciliation and safety monitoring.

        Args:
            patient_dfn: Patient's unique identifier (DFN) in the Vista system
            station: Vista station number for multi-site access (default: user's home station)
            active_only: When True, returns only active medications;
                        when False, includes discontinued and completed (default: True)
            therapeutic_class: Filter by therapeutic class (optional), examples:
                - "ANTIHYPERTENSIVE" - Blood pressure medications
                - "DIABETES" - Diabetes medications
                - "ANTICOAGULANT" - Blood thinners
                - "ANTIDEPRESSANT" - Depression medications
            limit: Maximum number of medications to return in all_medications array,
                  range 1-200 (default: 50). Summary counts and groupings include all medications.

        Returns:
            Medication data including:
            - Current active medications with dosing instructions
            - Medication history and status changes
            - Refill information and adherence tracking
            - Potential drug interactions and alerts
            - Therapeutic class groupings for medication review (includes all medications)
            - Prescriber information and pharmacy details
            - all_medications array limited by the limit parameter for performance
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return {
                "success": False,
                "error": "Invalid patient DFN format. DFN must be numeric.",
                "metadata": build_metadata(station=station),
            }

        # Validate limit parameter
        if limit < 1 or limit > 200:
            return {
                "success": False,
                "error": "Limit must be between 1 and 200.",
                "metadata": build_metadata(station=station),
            }

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter medications
            medications = patient_data.medications
            if active_only:
                medications = [m for m in medications if m.is_active]

            # Filter by therapeutic class
            if therapeutic_class:
                medications = [
                    m
                    for m in medications
                    if (
                        m.therapeutic_class
                        and therapeutic_class.upper() in m.therapeutic_class.upper()
                    )
                    or (m.va_class and therapeutic_class.upper() in m.va_class.upper())
                ]

            # Group medications by therapeutic class for better organization
            medication_groups: dict[str, list[Any]] = {}
            for med in medications:
                group_key = med.therapeutic_class or med.va_class or "Other"
                if group_key not in medication_groups:
                    medication_groups[group_key] = []
                medication_groups[group_key].append(med)

            # Identify medications needing refills soon
            refill_alerts = [m for m in medications if m.needs_refill_soon]

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                    "age": patient_data.demographics.age,
                },
                "medications": {
                    "total": len(patient_data.medications),
                    "active": len([m for m in patient_data.medications if m.is_active]),
                    "discontinued": len(
                        [m for m in patient_data.medications if m.is_discontinued]
                    ),
                    "filtered_count": len(medications),
                    "refill_alerts": len(refill_alerts),
                    "filters": {
                        "active_only": active_only,
                        "therapeutic_class": therapeutic_class,
                    },
                    "refill_alerts_list": [
                        {
                            "name": med.display_name,
                            "days_remaining": med.days_until_refill_needed,
                            "last_filled": (
                                med.last_filled.isoformat() if med.last_filled else None
                            ),
                            "prescriber": med.prescriber,
                        }
                        for med in refill_alerts
                    ],
                    "by_therapeutic_class": {
                        group: {
                            "count": len(meds),
                            "medications": [
                                {
                                    "name": med.display_name,
                                    "generic_name": med.generic_name,
                                    "dosage": med.dosage,
                                    "frequency": med.display_frequency,
                                    "route": med.route,
                                    "instructions": med.sig,
                                    "status": med.status,
                                    "started": med.start_date.isoformat(),
                                    "ended": (
                                        med.end_date.isoformat()
                                        if med.end_date
                                        else None
                                    ),
                                    "prescriber": med.prescriber,
                                    "refills_remaining": med.refills_remaining,
                                    "days_supply": med.days_supply,
                                    "needs_refill": med.needs_refill_soon,
                                }
                                for med in meds
                            ],
                        }
                        for group, meds in medication_groups.items()
                    },
                    "all_medications": [
                        {
                            "id": med.local_id,
                            "name": med.display_name,
                            "generic_name": med.generic_name,
                            "brand_name": med.brand_name,
                            "strength": med.strength,
                            "dosage_form": med.dosage,
                            "frequency": med.display_frequency,
                            "route": med.route,
                            "instructions": med.sig,
                            "status": med.status,
                            "active": med.is_active,
                            "discontinued": med.is_discontinued,
                            "start_date": med.start_date.isoformat(),
                            "end_date": (
                                med.end_date.isoformat() if med.end_date else None
                            ),
                            "last_filled": (
                                med.last_filled.isoformat() if med.last_filled else None
                            ),
                            "prescriber": med.prescriber,
                            "pharmacy": med.pharmacy,
                            "quantity": med.quantity,
                            "days_supply": med.days_supply,
                            "refills_remaining": med.refills_remaining,
                            "therapeutic_class": med.therapeutic_class,
                            "va_class": med.va_class,
                            "patient_instructions": med.patient_instructions,
                            "needs_refill": med.needs_refill_soon,
                            "days_until_refill": med.days_until_refill_needed,
                        }
                        for med in medications[:limit]  # Limit based on parameter
                    ],
                },
                "metadata": {
                    **build_metadata(
                        station=station,
                        duration_ms=int((time.time() - start_time) * 1000),
                    ),
                    "rpc": {
                        "rpc": "VPR GET PATIENT DATA JSON",
                        "context": "LHS RPC CONTEXT",
                        "jsonResult": True,
                        "parameters": [{"namedArray": {"patientId": patient_dfn}}],
                    },
                    "duz": caller_duz,
                },
            }

        except Exception as e:
            logger.error(
                f"🩺 [DEBUG] Exception in get_patient_medications: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_medications")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }

    @mcp.tool()
    async def get_patient_health_factors(
        patient_dfn: str,
        station: str | None = None,
        category_filter: str | None = None,
        risk_category: str | None = None,
        severity_filter: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Retrieve health factors and risk factors for a specific patient

        Provides comprehensive health factor analysis including lifestyle, environmental,
        and genetic risk factors. Essential for risk assessment, preventive care planning,
        and health maintenance tracking.

        Args:
            patient_dfn: Patient's unique identifier (DFN) in the Vista system
            station: Vista station number for multi-site access (default: user's home station)
            category_filter: Filter by specific category (optional), examples:
                - "COVID-19" - COVID-related factors
                - "CANCER SCREENING" - Cancer screening factors
                - "SUBSTANCE" - Substance use factors
                - "EXPOSURE" - Environmental exposure factors
            risk_category: Filter by risk type (optional):
                - "lifestyle" - Modifiable lifestyle factors (smoking, diet, exercise)
                - "environmental" - Environmental exposures (agent orange, radiation)
                - "genetic" - Genetic/hereditary factors
                - "medical" - Medical conditions and diagnoses
                - "screening" - Screening and preventive measures
            severity_filter: Filter by severity level (optional):
                - "mild" - Low-risk factors
                - "moderate" - Moderate-risk factors
                - "severe" - High-risk factors
            limit: Maximum number of health factors to return in all_health_factors array,
                  range 1-200 (default: 50). Summary counts and groupings include all factors.

        Returns:
            Health factor data including:
            - Current active health factors with risk assessment
            - Categorized factors by type (lifestyle, environmental, genetic)
            - Risk scores and severity levels for clinical decision support
            - Health factor trends and progression over time
            - Modifiable vs non-modifiable risk factor identification
            - Health maintenance and screening recommendations
            - all_health_factors array limited by the limit parameter for performance
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return {
                "success": False,
                "error": "Invalid patient DFN format. DFN must be numeric.",
                "metadata": build_metadata(station=station),
            }

        # Validate limit parameter
        if limit < 1 or limit > 200:
            return {
                "success": False,
                "error": "Limit must be between 1 and 200.",
                "metadata": build_metadata(station=station),
            }

        try:
            # Get patient data (handles caching internally)
            patient_data = await get_patient_data(
                vista_client, station, patient_dfn, caller_duz
            )

            # Filter health factors
            health_factors = patient_data.health_factors

            # Filter by category
            if category_filter:
                health_factors = [
                    f
                    for f in health_factors
                    if category_filter.upper() in f.category.upper()
                ]

            # Filter by risk category
            if risk_category:
                health_factors = [
                    f
                    for f in health_factors
                    if f.risk_category.lower() == risk_category.lower()
                ]

            # Filter by severity
            if severity_filter:
                health_factors = [
                    f
                    for f in health_factors
                    if f.severity_level.lower() == severity_filter.lower()
                ]

            # Group factors by risk category
            from ...services.validators.clinical_validators import (
                get_health_factor_trends,
            )

            factor_groups: dict[str, list[Any]] = {}
            for factor in health_factors:
                group_key = factor.risk_category
                if group_key not in factor_groups:
                    factor_groups[group_key] = []
                factor_groups[group_key].append(factor)

            # Identify high-risk factors
            high_risk_factors = [f for f in health_factors if f.risk_score >= 7]

            # Identify modifiable factors
            modifiable_factors = [f for f in health_factors if f.is_modifiable]

            # Get factors requiring monitoring
            monitoring_factors = [f for f in health_factors if f.requires_monitoring]

            # Calculate trending for common factors
            trending_data = {}
            common_factor_names = list({f.factor_name for f in health_factors})[
                :10
            ]  # Top 10
            for factor_name in common_factor_names:
                trending_data[factor_name] = get_health_factor_trends(
                    health_factors, factor_name
                )

            return {
                "success": True,
                "data": {
                    "patient_dfn": patient_dfn,
                    "patient_name": patient_data.patient_name,
                    "total_health_factors": len(patient_data.health_factors),
                    "filtered_count": len(health_factors),
                    "summary": {
                        "high_risk_count": len(high_risk_factors),
                        "modifiable_count": len(modifiable_factors),
                        "monitoring_required_count": len(monitoring_factors),
                        "average_risk_score": (
                            round(
                                sum(f.risk_score for f in health_factors)
                                / len(health_factors),
                                1,
                            )
                            if health_factors
                            else 0.0
                        ),
                    },
                    "by_risk_category": {
                        group: {
                            "count": len(factors),
                            "average_risk_score": (
                                round(
                                    sum(f.risk_score for f in factors) / len(factors), 1
                                )
                                if factors
                                else 0.0
                            ),
                            "factors": [
                                {
                                    "name": factor.factor_name,
                                    "category": factor.category,
                                    "severity": factor.severity_level,
                                    "risk_score": factor.risk_score,
                                    "recorded_date": factor.recorded_date.isoformat(),
                                    "is_modifiable": factor.is_modifiable,
                                    "requires_monitoring": factor.requires_monitoring,
                                    "facility": factor.facility_name,
                                }
                                for factor in factors
                            ],
                        }
                        for group, factors in factor_groups.items()
                    },
                    "high_risk_factors": [
                        {
                            "name": factor.factor_name,
                            "category": factor.category,
                            "risk_category": factor.risk_category,
                            "severity": factor.severity_level,
                            "risk_score": factor.risk_score,
                            "recorded_date": factor.recorded_date.isoformat(),
                            "is_modifiable": factor.is_modifiable,
                            "comments": factor.comments,
                        }
                        for factor in high_risk_factors
                    ],
                    "trending": trending_data,
                    "all_health_factors": [
                        {
                            "id": factor.local_id,
                            "uid": factor.uid,
                            "name": factor.factor_name,
                            "category": factor.category,
                            "risk_category": factor.risk_category,
                            "severity": factor.severity_level,
                            "status": factor.status,
                            "risk_score": factor.risk_score,
                            "recorded_date": factor.recorded_date.isoformat(),
                            "recorded_by": factor.recorded_by,
                            "facility": factor.facility_name,
                            "encounter": factor.encounter_name,
                            "location": factor.location_name,
                            "comments": factor.comments,
                            "is_modifiable": factor.is_modifiable,
                            "requires_monitoring": factor.requires_monitoring,
                            "summary": factor.summary,
                        }
                        for factor in health_factors[:limit]  # Limit based on parameter
                    ],
                },
                "metadata": {
                    **build_metadata(
                        station=station,
                        duration_ms=int((time.time() - start_time) * 1000),
                    ),
                    "rpc": {
                        "rpc": "VPR GET PATIENT DATA JSON",
                        "context": "LHS RPC CONTEXT",
                        "jsonResult": True,
                        "parameters": [{"namedArray": {"patientId": patient_dfn}}],
                    },
                    "duz": caller_duz,
                },
            }

        except Exception as e:
            logger.error(
                f"🩺 [DEBUG] Exception in get_patient_health_factors: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_health_factors")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
