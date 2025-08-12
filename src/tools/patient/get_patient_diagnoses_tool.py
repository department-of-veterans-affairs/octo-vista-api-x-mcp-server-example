"""Get patient diagnoses tool for MCP server"""

import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...models.responses.tool_responses import PatientDiagnosesResponse
from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import (
    build_metadata,
    build_pagination_metadata,
    get_default_duz,
    get_default_station,
    get_logger,
)
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_diagnoses_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_diagnoses tool with the MCP server"""

    @mcp.tool()
    async def get_patient_diagnoses(
        patient_dfn: str,
        station: str | None = None,
        body_system: str | None = None,
        diagnosis_type: str | None = None,
        status_filter: str | None = None,
        icd_version: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> PatientDiagnosesResponse | dict[str, Any]:
        """Get patient diagnoses with ICD codes."""
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

            # Filter diagnoses
            diagnoses = patient_data.diagnoses

            # Filter by body system
            if body_system:
                diagnoses = [
                    d for d in diagnoses if d.body_system.lower() == body_system.lower()
                ]

            # Filter by diagnosis type
            if diagnosis_type:
                diagnoses = [
                    d
                    for d in diagnoses
                    if d.diagnosis_type.lower() == diagnosis_type.lower()
                ]

            # Filter by status
            if status_filter:
                if status_filter.lower() == "chronic":
                    diagnoses = [d for d in diagnoses if d.is_chronic]
                else:
                    diagnoses = [
                        d
                        for d in diagnoses
                        if d.status.lower() == status_filter.lower()
                    ]

            # Filter by ICD version
            if icd_version:
                diagnoses = [
                    d for d in diagnoses if d.icd_version.upper() == icd_version.upper()
                ]

            # Apply pagination
            total_diagnoses = len(diagnoses)
            diagnoses_page = diagnoses[offset : offset + limit]

            # Group diagnoses by body system (use paginated results)
            from ...services.validators.clinical_validators import get_diagnosis_trends

            diagnosis_groups: dict[str, list[Any]] = {}
            for diagnosis in diagnoses_page:
                group_key = diagnosis.body_system
                if group_key not in diagnosis_groups:
                    diagnosis_groups[group_key] = []
                diagnosis_groups[group_key].append(diagnosis)

            # Identify primary diagnoses (from paginated results)
            primary_diagnoses = [d for d in diagnoses_page if d.is_primary]

            # Identify chronic conditions (from paginated results)
            chronic_diagnoses = [d for d in diagnoses_page if d.is_chronic]

            # Get active diagnoses (from paginated results)
            active_diagnoses = [
                d for d in diagnoses_page if d.status.lower() == "active"
            ]

            # Calculate trending for common diagnoses (from paginated results)
            trending_data = {}
            common_icd_codes = list({d.icd_code for d in diagnoses_page if d.icd_code})[
                :10
            ]  # Top 10
            for icd_code in common_icd_codes:
                trending_data[icd_code] = get_diagnosis_trends(diagnoses_page, icd_code)

            return PatientDiagnosesResponse(
                success=True,
                data={
                    "patient_dfn": patient_dfn,
                    "patient_name": patient_data.patient_name,
                    "total_diagnoses": len(patient_data.diagnoses),
                    "filtered_count": len(diagnoses_page),
                    "pagination": build_pagination_metadata(
                        total_items=total_diagnoses,
                        returned_items=len(diagnoses_page),
                        offset=offset,
                        limit=limit,
                        tool_name="get_patient_diagnoses",
                        patient_dfn=patient_dfn,
                        station=station,
                        body_system=body_system,
                        diagnosis_type=diagnosis_type,
                        status_filter=status_filter,
                        icd_version=icd_version,
                    ),
                    "summary": {
                        "primary_count": len(primary_diagnoses),
                        "chronic_count": len(chronic_diagnoses),
                        "active_count": len(active_diagnoses),
                        "icd_9_count": len(
                            [d for d in diagnoses if d.icd_version == "ICD-9"]
                        ),
                        "icd_10_count": len(
                            [d for d in diagnoses if d.icd_version == "ICD-10"]
                        ),
                    },
                    "by_body_system": {
                        system: {
                            "count": len(system_diagnoses),
                            "primary_count": len(
                                [d for d in system_diagnoses if d.is_primary]
                            ),
                            "chronic_count": len(
                                [d for d in system_diagnoses if d.is_chronic]
                            ),
                            "diagnoses": [
                                {
                                    "icd_code": diagnosis.icd_code,
                                    "description": diagnosis.description,
                                    "diagnosis_type": diagnosis.diagnosis_type,
                                    "status": diagnosis.status,
                                    "severity": diagnosis.severity_level,
                                    "is_chronic": diagnosis.is_chronic,
                                    "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
                                    "provider": diagnosis.provider,
                                    "facility": diagnosis.facility_name,
                                }
                                for diagnosis in system_diagnoses
                            ],
                        }
                        for system, system_diagnoses in diagnosis_groups.items()
                    },
                    "primary_diagnoses": [
                        {
                            "icd_code": diagnosis.icd_code,
                            "icd_version": diagnosis.icd_version,
                            "description": diagnosis.description,
                            "body_system": diagnosis.body_system,
                            "severity": diagnosis.severity_level,
                            "status": diagnosis.status,
                            "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
                            "is_chronic": diagnosis.is_chronic,
                            "provider": diagnosis.provider,
                        }
                        for diagnosis in primary_diagnoses
                    ],
                    "chronic_conditions": [
                        {
                            "icd_code": diagnosis.icd_code,
                            "description": diagnosis.description,
                            "body_system": diagnosis.body_system,
                            "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
                            "severity": diagnosis.severity_level,
                            "status": diagnosis.status,
                        }
                        for diagnosis in chronic_diagnoses
                    ],
                    "trending": trending_data,
                    "all_diagnoses": [
                        {
                            "id": diagnosis.local_id,
                            "uid": diagnosis.uid,
                            "icd_code": diagnosis.icd_code,
                            "icd_version": diagnosis.icd_version,
                            "description": diagnosis.description,
                            "body_system": diagnosis.body_system,
                            "diagnosis_type": diagnosis.diagnosis_type,
                            "status": diagnosis.status,
                            "severity": diagnosis.severity_level,
                            "diagnosis_date": diagnosis.diagnosis_date.isoformat(),
                            "provider": diagnosis.provider,
                            "provider_uid": diagnosis.provider_uid,
                            "facility": diagnosis.facility_name,
                            "encounter": diagnosis.encounter_name,
                            "associated_visit_uid": diagnosis.associated_visit_uid,
                            "comments": diagnosis.comments,
                            "is_primary": diagnosis.is_primary,
                            "is_chronic": diagnosis.is_chronic,
                            "is_valid_icd": diagnosis.is_valid_icd,
                            "summary": diagnosis.summary,
                        }
                        for diagnosis in diagnoses_page
                    ],
                },
                metadata={
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
            )

        except Exception as e:
            logger.error(
                f"🩺 [DEBUG] Exception in get_patient_diagnoses: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Unexpected error in get_patient_diagnoses")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station),
            }
