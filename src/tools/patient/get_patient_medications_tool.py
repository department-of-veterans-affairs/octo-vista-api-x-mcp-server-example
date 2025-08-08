"""Get patient medications tool for MCP server"""

import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import build_metadata, get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger(__name__)


def register_get_patient_medications_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_medications tool with the MCP server"""

    @mcp.tool()
    async def get_patient_medications(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
        therapeutic_class: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get patient medications with dosing and refill information."""
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
                    "age": patient_data.demographics.calculate_age(),
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
                                    "started": (
                                        med.start_date.isoformat()
                                        if med.start_date
                                        else None
                                    ),
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
                            "start_date": (
                                med.start_date.isoformat() if med.start_date else None
                            ),
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
