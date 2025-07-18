"""Patient-related MCP tools using cached VPR data"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...models.patient.patient import PatientDataCollection
from ...models.responses import PatientSearchResponse
from ...services.cache.factory import CacheFactory
from ...services.parsers.patient.patient_parser import parse_vpr_patient_data
from ...services.parsers.vista import parse_patient_search
from ...utils import (
    build_metadata,
    get_default_duz,
    get_default_station,
    log_rpc_call,
    translate_vista_error,
    validate_dfn,
)
from ...vista.base import BaseVistaClient, VistaAPIError

logger = logging.getLogger(__name__)


def register_patient_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register patient-related tools with the MCP server"""

    # Create patient cache
    patient_cache = None

    async def get_patient_cache():
        """Get or create patient cache instance"""
        nonlocal patient_cache
        if patient_cache is None:
            patient_cache = await CacheFactory.create_patient_cache()
        return patient_cache

    def format_vital_type(type_name: str) -> str:
        """Convert vital type name to snake_case"""
        # Map common vital types to clean snake_case names
        vital_type_map = {
            "BLOOD PRESSURE": "blood_pressure",
            "PULSE OXIMETRY": "pulse_oximetry",
            "TEMPERATURE": "temperature",
            "RESPIRATION": "respiration",
            "PULSE": "pulse",
            "WEIGHT": "weight",
            "HEIGHT": "height",
            "PAIN": "pain",
            "BMI": "bmi",
        }
        return vital_type_map.get(
            type_name.upper(), type_name.lower().replace(" ", "_")
        )

    def format_lab_type(type_name: str) -> str:
        """Convert lab type name to snake_case"""
        if not type_name:
            return "unknown"
        # Common lab types that need special formatting
        lab_type_map = {
            "GLUCOSE": "glucose",
            "HEMOGLOBIN": "hemoglobin",
            "HEMATOCRIT": "hematocrit",
            "WBC": "wbc",
            "RBC": "rbc",
            "PLATELET COUNT": "platelet_count",
            "SODIUM": "sodium",
            "POTASSIUM": "potassium",
            "CHLORIDE": "chloride",
            "CO2": "co2",
            "BUN": "bun",
            "CREATININE": "creatinine",
            "CALCIUM": "calcium",
            "TOTAL PROTEIN": "total_protein",
            "ALBUMIN": "albumin",
            "BILIRUBIN": "bilirubin",
            "ALT": "alt",
            "AST": "ast",
            "CHOLESTEROL": "cholesterol",
            "TRIGLYCERIDES": "triglycerides",
            "HDL": "hdl",
            "LDL": "ldl",
            "TSH": "tsh",
            "T4": "t4",
            "T3": "t3",
            "HBA1C": "hba1c",
            "PSA": "psa",
            "INR": "inr",
            "PT": "pt",
            "PTT": "ptt",
        }
        # Check if we have a specific mapping
        normalized = type_name.upper()
        if normalized in lab_type_map:
            return lab_type_map[normalized]
        # Otherwise, convert to snake_case
        return type_name.lower().replace(" ", "_").replace("-", "_").replace("/", "_")

    def format_service_name(service: str) -> str:
        """Convert service name to proper case"""
        if not service:
            return "unknown"
        # Special cases that need specific formatting
        service_map = {
            "CARDIOLOGY": "Cardiology",
            "COM-CARE CARDIOLOGY": "Community Care Cardiology",
            "AUDIOLOGY OUTPATIENT": "Audiology Outpatient",
            "AUDIOLOGY": "Audiology",
            "DERMATOLOGY": "Dermatology",
            "ENDOCRINOLOGY": "Endocrinology",
            "GASTROENTEROLOGY": "Gastroenterology",
            "HEMATOLOGY": "Hematology",
            "INFECTIOUS DISEASE": "Infectious Disease",
            "NEPHROLOGY": "Nephrology",
            "NEUROLOGY": "Neurology",
            "ONCOLOGY": "Oncology",
            "OPHTHALMOLOGY": "Ophthalmology",
            "ORTHOPEDICS": "Orthopedics",
            "PSYCHIATRY": "Psychiatry",
            "PULMONARY": "Pulmonary",
            "RHEUMATOLOGY": "Rheumatology",
            "UROLOGY": "Urology",
        }
        # Check if we have a specific mapping
        normalized = service.upper()
        if normalized in service_map:
            return service_map[normalized]
        # Otherwise, convert to title case
        return " ".join(word.capitalize() for word in service.split())

    def format_status(status: str) -> str:
        """Convert status to lowercase"""
        if not status:
            return "unknown"
        return status.lower()

    def format_urgency(urgency: str) -> str:
        """Convert urgency to lowercase"""
        if not urgency:
            return "routine"
        return urgency.lower()

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
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORWPT LIST",
                parameters=[{"string": f"^{search_term.upper()}"}],
            )

            # Parse results
            patients = parse_patient_search(result)

            # Add station to each patient
            for patient in patients:
                patient.station = station

            # Limit results
            if limit and len(patients) > limit:
                patients = patients[:limit]

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORWPT LIST",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            # Build response
            response = PatientSearchResponse(
                success=True,
                search_term=search_term,
                station=station,
                count=len(patients),
                patients=patients,
                metadata=build_metadata(
                    station=station,
                    rpc_name="ORWPT LIST",
                    duration_ms=duration_ms,
                ),
            )

            return response.model_dump()

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWPT LIST",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return PatientSearchResponse.error_response(
                error=translate_vista_error(e.to_dict()),
                metadata=build_metadata(station=station, rpc_name="ORWPT LIST"),
            ).model_dump()

        except Exception as e:
            logger.exception("Unexpected error in search_patients")
            return PatientSearchResponse.error_response(
                error=f"Unexpected error: {str(e)}",
                metadata=build_metadata(station=station, rpc_name="ORWPT LIST"),
            ).model_dump()

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
            # Get patient data from cache
            cache = await get_patient_cache()
            cached_data = await cache.get_patient_data(station, patient_dfn, caller_duz)

            if cached_data:
                # Deserialize from cache
                patient_data = PatientDataCollection(**cached_data)
            else:
                # Fetch from VistA
                result = await vista_client.invoke_rpc(
                    station=station,
                    caller_duz=caller_duz,
                    rpc_name="VPR GET PATIENT DATA JSON",
                    context="VPR APPLICATION PROXY",
                    parameters=[{"namedArray": {"patientId": patient_dfn}}],
                    json_result=True,
                )

                # Parse and cache
                patient_data = parse_vpr_patient_data(result, station, patient_dfn)
                await cache.set_patient_data(
                    station, patient_dfn, caller_duz, patient_data.model_dump()
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
                "metadata": build_metadata(
                    station=station,
                    rpc_name="get_patient_vitals",
                    duration_ms=int((time.time() - start_time) * 1000),
                ),
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
            # Get patient data from cache
            cache = await get_patient_cache()
            cached_data = await cache.get_patient_data(station, patient_dfn, caller_duz)

            if cached_data:
                # Deserialize from cache
                patient_data = PatientDataCollection(**cached_data)
            else:
                # Fetch from VistA
                result = await vista_client.invoke_rpc(
                    station=station,
                    caller_duz=caller_duz,
                    rpc_name="VPR GET PATIENT DATA JSON",
                    context="VPR APPLICATION PROXY",
                    parameters=[{"namedArray": {"patientId": patient_dfn}}],
                    json_result=True,
                )

                # Parse and cache
                patient_data = parse_vpr_patient_data(result, station, patient_dfn)
                await cache.set_patient_data(
                    station, patient_dfn, caller_duz, patient_data.model_dump()
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
                "metadata": build_metadata(
                    station=station,
                    rpc_name="get_patient_labs",
                    duration_ms=int((time.time() - start_time) * 1000),
                ),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_labs")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }

    @mcp.tool()
    async def get_patient_summary(
        patient_dfn: str,
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a comprehensive clinical summary for a specific patient

        Provides a complete overview of the patient's current health status by
        aggregating demographics, vital signs, laboratory results, and consultations.
        Ideal for quick patient reviews, handoffs, or generating reports.

        Args:
            patient_dfn: Patient's unique identifier (DFN) in the Vista system
            station: Vista station number for multi-site access (default: user's home station)

        Returns:
            Comprehensive patient summary containing:
            - Demographics: Name, age, gender, contact info, emergency contacts
            - Insurance and eligibility information
            - Latest vital signs for all types
            - Recent abnormal lab results (up to 10 most critical)
            - Active consultation requests with urgency levels
            - Patient flags (allergies, alerts, advance directives)
            - Primary care team and provider information
            Data freshness timestamp included for cache management
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
            # Get patient data from cache
            cache = await get_patient_cache()
            cached_data = await cache.get_patient_data(station, patient_dfn, caller_duz)

            if cached_data:
                # Deserialize from cache
                patient_data = PatientDataCollection(**cached_data)
            else:
                # Fetch from VistA
                result = await vista_client.invoke_rpc(
                    station=station,
                    caller_duz=caller_duz,
                    rpc_name="VPR GET PATIENT DATA JSON",
                    context="VPR APPLICATION PROXY",
                    parameters=[{"namedArray": {"patientId": patient_dfn}}],
                    json_result=True,
                )

                # Parse and cache
                patient_data = parse_vpr_patient_data(result, station, patient_dfn)
                await cache.set_patient_data(
                    station, patient_dfn, caller_duz, patient_data.model_dump()
                )

            # Get demographics
            demographics = patient_data.demographics

            # Get latest vitals
            latest_vitals = patient_data.get_latest_vitals()

            # Get recent abnormal labs
            abnormal_labs = patient_data.get_abnormal_labs()[:10]  # Top 10

            # Get active consults
            active_consults = patient_data.get_active_consults()

            # Build summary
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "icn": demographics.icn,
                    "name": demographics.full_name,
                    "ssn": demographics.ssn,
                    "dob": demographics.date_of_birth.isoformat(),
                    "age": demographics.calculate_age(),
                    "gender": demographics.gender_name,
                    "phone": demographics.primary_phone,
                    "address": (
                        {
                            "street": (
                                demographics.primary_address.street_line1
                                if demographics.primary_address
                                else None
                            ),
                            "city": (
                                demographics.primary_address.city
                                if demographics.primary_address
                                else None
                            ),
                            "state": (
                                demographics.primary_address.state_province
                                if demographics.primary_address
                                else None
                            ),
                            "zip": (
                                demographics.primary_address.postal_code
                                if demographics.primary_address
                                else None
                            ),
                        }
                        if demographics.primary_address
                        else None
                    ),
                    "emergency_contact": (
                        {
                            "name": (
                                demographics.emergency_contact.name
                                if demographics.emergency_contact
                                else None
                            ),
                            "relationship": (
                                demographics.emergency_contact.relationship
                                if demographics.emergency_contact
                                else None
                            ),
                            "phone": (
                                demographics.emergency_contact.phone
                                if demographics.emergency_contact
                                else None
                            ),
                        }
                        if demographics.emergency_contact
                        else None
                    ),
                    "flags": [
                        {"name": flag.name, "high_risk": flag.is_high_risk}
                        for flag in demographics.flags
                    ],
                },
                "clinical_summary": {
                    "vitals": {
                        format_vital_type(type_name): {
                            "value": vital.display_value,
                            "date": vital.observed.isoformat(),
                            "abnormal": vital.is_abnormal,
                        }
                        for type_name, vital in latest_vitals.items()
                    },
                    "abnormal_labs": [
                        {
                            "test": lab.type_name,
                            "value": lab.display_value,
                            "date": lab.observed.isoformat(),
                            "critical": lab.is_critical,
                            "interpretation": lab.interpretation_name,
                        }
                        for lab in abnormal_labs
                    ],
                    "active_consults": [
                        {
                            "service": format_service_name(consult.service),
                            "status": format_status(consult.status_name),
                            "urgency": format_urgency(consult.urgency),
                            "ordered": consult.date_time.isoformat(),
                            "overdue": consult.is_overdue,
                            "reason": consult.reason,
                        }
                        for consult in active_consults
                    ],
                },
                "data_summary": {
                    "total_items": patient_data.total_items,
                    "vital_signs": len(patient_data.vital_signs),
                    "lab_results": len(patient_data.lab_results),
                    "consults": len(patient_data.consults),
                    "data_age_minutes": (
                        datetime.now(patient_data.retrieved_at.tzinfo)
                        - patient_data.retrieved_at
                    ).total_seconds()
                    / 60,
                },
                "metadata": build_metadata(
                    station=station,
                    rpc_name="get_patient_summary",
                    duration_ms=int((time.time() - start_time) * 1000),
                ),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_summary")
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
            # Get patient data from cache
            cache = await get_patient_cache()
            cached_data = await cache.get_patient_data(station, patient_dfn, caller_duz)

            if cached_data:
                # Deserialize from cache
                patient_data = PatientDataCollection(**cached_data)
            else:
                # Fetch from VistA
                result = await vista_client.invoke_rpc(
                    station=station,
                    caller_duz=caller_duz,
                    rpc_name="VPR GET PATIENT DATA JSON",
                    context="VPR APPLICATION PROXY",
                    parameters=[{"namedArray": {"patientId": patient_dfn}}],
                    json_result=True,
                )

                # Parse and cache
                patient_data = parse_vpr_patient_data(result, station, patient_dfn)
                await cache.set_patient_data(
                    station, patient_dfn, caller_duz, patient_data.model_dump()
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
                "metadata": build_metadata(
                    station=station,
                    rpc_name="get_patient_consults",
                    duration_ms=int((time.time() - start_time) * 1000),
                ),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_consults")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
