"""Clinical data MCP tools"""

import logging
import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...models.responses import (
    LabResultsResponse,
    MedicationsResponse,
    VitalSignsResponse,
)
from ...services.parsers.vista import (
    parse_allergies,
    parse_lab_results,
    parse_medications,
    parse_problems,
    parse_vital_signs,
)
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


def register_clinical_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register clinical data tools with the MCP server"""

    @mcp.tool()
    async def get_medications(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """
        Get patient medications

        Args:
            patient_dfn: Patient's DFN
            station: Vista station number (default: configured default)
            active_only: Return only active medications (default: True)

        Returns:
            Structured list of medications with dosing information
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return MedicationsResponse.error_response(
                error="Invalid patient DFN format. DFN must be numeric.",
                metadata=build_metadata(station=station),
            ).model_dump()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORWPS ACTIVE",
                parameters=[{"string": patient_dfn}],
            )

            # Parse medications
            all_medications = parse_medications(result)

            # Filter if active_only
            if active_only:
                medications = [m for m in all_medications if m.status == "ACTIVE"]
            else:
                medications = all_medications

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORWPS ACTIVE",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            # Build response
            response = MedicationsResponse(
                success=True,
                patient_dfn=patient_dfn,
                station=station,
                count=len(medications),
                medications=medications,
                metadata=build_metadata(
                    station=station,
                    rpc_name="ORWPS ACTIVE",
                    duration_ms=duration_ms,
                ),
            )

            return response.model_dump()

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWPS ACTIVE",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return MedicationsResponse.error_response(
                error=translate_vista_error(e.to_dict()),
                metadata=build_metadata(station=station, rpc_name="ORWPS ACTIVE"),
            ).model_dump()

        except Exception as e:
            logger.exception("Unexpected error in get_medications")
            return MedicationsResponse.error_response(
                error=f"Unexpected error: {str(e)}",
                metadata=build_metadata(station=station, rpc_name="ORWPS ACTIVE"),
            ).model_dump()

    @mcp.tool()
    async def get_lab_results(
        patient_dfn: str,
        station: str | None = None,
        days_back: int = 30,
        max_results: int = 50,
    ) -> dict[str, Any]:
        """
        Get patient laboratory results

        Args:
            patient_dfn: Patient's DFN
            station: Vista station number (default: configured default)
            days_back: Number of days to look back (default: 30)
            max_results: Maximum number of results (default: 50)

        Returns:
            Structured list of lab results with values and reference ranges
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return LabResultsResponse.error_response(
                error="Invalid patient DFN format. DFN must be numeric.",
                metadata=build_metadata(station=station),
            ).model_dump()

        try:
            # Build parameters
            parameters = [
                {"string": patient_dfn},
                {"string": ""},  # Start date (empty = use days_back)
                {"string": ""},  # End date
                {"string": str(max_results)},
                {"string": ""},  # Reverse chronological
                {"string": ""},  # Format
                {"string": str(days_back)},
            ]

            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORWLRR INTERIM",
                parameters=parameters,
            )

            # Parse lab results
            lab_results = parse_lab_results(result)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORWLRR INTERIM",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            # Build response
            response = LabResultsResponse(
                success=True,
                patient_dfn=patient_dfn,
                station=station,
                count=len(lab_results),
                lab_results=lab_results,
                metadata=build_metadata(
                    station=station,
                    rpc_name="ORWLRR INTERIM",
                    duration_ms=duration_ms,
                ),
            )

            return response.model_dump()

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWLRR INTERIM",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return LabResultsResponse.error_response(
                error=translate_vista_error(e.to_dict()),
                metadata=build_metadata(station=station, rpc_name="ORWLRR INTERIM"),
            ).model_dump()

        except Exception as e:
            logger.exception("Unexpected error in get_lab_results")
            return LabResultsResponse.error_response(
                error=f"Unexpected error: {str(e)}",
                metadata=build_metadata(station=station, rpc_name="ORWLRR INTERIM"),
            ).model_dump()

    @mcp.tool()
    async def get_vital_signs(
        patient_dfn: str,
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Get patient vital signs

        Args:
            patient_dfn: Patient's DFN
            station: Vista station number (default: configured default)

        Returns:
            Structured list of vital sign measurements
        """
        start_time = time.time()
        station = station or get_default_station()
        caller_duz = get_default_duz()

        # Validate DFN
        if not validate_dfn(patient_dfn):
            return VitalSignsResponse.error_response(
                error="Invalid patient DFN format. DFN must be numeric.",
                metadata=build_metadata(station=station),
            ).model_dump()

        try:
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORQQVI VITALS",
                parameters=[{"string": patient_dfn}],
            )

            # Parse vital signs
            vital_signs = parse_vital_signs(result)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORQQVI VITALS",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            # Build response
            response = VitalSignsResponse(
                success=True,
                patient_dfn=patient_dfn,
                station=station,
                count=len(vital_signs),
                vital_signs=vital_signs,
                metadata=build_metadata(
                    station=station,
                    rpc_name="ORQQVI VITALS",
                    duration_ms=duration_ms,
                ),
            )

            return response.model_dump()

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORQQVI VITALS",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return VitalSignsResponse.error_response(
                error=translate_vista_error(e.to_dict()),
                metadata=build_metadata(station=station, rpc_name="ORQQVI VITALS"),
            ).model_dump()

        except Exception as e:
            logger.exception("Unexpected error in get_vital_signs")
            return VitalSignsResponse.error_response(
                error=f"Unexpected error: {str(e)}",
                metadata=build_metadata(station=station, rpc_name="ORQQVI VITALS"),
            ).model_dump()

    @mcp.tool()
    async def get_problems(
        patient_dfn: str,
        station: str | None = None,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """
        Get patient problem list

        Args:
            patient_dfn: Patient's DFN
            station: Vista station number (default: configured default)
            active_only: Return only active problems (default: True)

        Returns:
            Structured list of medical problems/diagnoses
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
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORQQPL PROBLEM LIST",
                parameters=[{"string": patient_dfn}],
            )

            # Parse problems
            all_problems = parse_problems(result)

            # Filter if active_only
            if active_only:
                problems = [
                    p for p in all_problems if p.status == "ACTIVE" or p.status == "A"
                ]
            else:
                problems = all_problems

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORQQPL PROBLEM LIST",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            return {
                "success": True,
                "patient_dfn": patient_dfn,
                "station": station,
                "count": len(problems),
                "problems": [p.model_dump() for p in problems],
                "active_only": active_only,
                "metadata": build_metadata(
                    station=station,
                    rpc_name="ORQQPL PROBLEM LIST",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORQQPL PROBLEM LIST",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(
                    station=station, rpc_name="ORQQPL PROBLEM LIST"
                ),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_problems")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(
                    station=station, rpc_name="ORQQPL PROBLEM LIST"
                ),
            }

    @mcp.tool()
    async def get_allergies(
        patient_dfn: str,
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Get patient allergies and adverse reactions

        Args:
            patient_dfn: Patient's DFN
            station: Vista station number (default: configured default)

        Returns:
            Structured list of allergies with reactions and severity
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
            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="ORQQAL LIST",
                parameters=[{"string": patient_dfn}],
            )

            # Parse allergies
            allergies = parse_allergies(result)

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORQQAL LIST",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            # Determine NKA status
            nka = len(allergies) == 0

            return {
                "success": True,
                "patient_dfn": patient_dfn,
                "station": station,
                "count": len(allergies),
                "allergies": [a.model_dump() for a in allergies],
                "nka": nka,  # No Known Allergies
                "metadata": build_metadata(
                    station=station,
                    rpc_name="ORQQAL LIST",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORQQAL LIST",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="ORQQAL LIST"),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_allergies")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="ORQQAL LIST"),
            }
