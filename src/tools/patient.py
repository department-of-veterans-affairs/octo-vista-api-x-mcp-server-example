"""Patient-related MCP tools"""

import logging
import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..api_clients.base import BaseVistaClient, VistaAPIError
from ..models import PatientSearchResponse, VprDomain
from ..parsers import parse_patient_demographics, parse_patient_search
from ..utils import (
    build_metadata,
    get_default_duz,
    get_default_station,
    log_rpc_call,
    translate_vista_error,
    validate_dfn,
)

logger = logging.getLogger(__name__)


def register_patient_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register patient-related tools with the MCP server"""

    @mcp.tool()
    async def search_patients(
        search_term: str,
        station: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Search for patients by name or SSN fragment

        Args:
            search_term: Patient name prefix (e.g., "SMI" for Smith) or last 4 SSN digits
            station: Vista station number (default: configured default)
            limit: Maximum number of results (default: 10)

        Returns:
            Structured patient search results with demographics
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
    async def get_patient_demographics(
        patient_dfn: str,
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Get detailed patient demographics

        Args:
            patient_dfn: Patient's DFN (internal ID)
            station: Vista station number (default: configured default)

        Returns:
            Complete patient demographic information
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
                rpc_name="ORWPT ID INFO",
                parameters=[{"string": patient_dfn}],
            )

            # Parse demographics
            demographics = parse_patient_demographics(result, patient_dfn)

            if not demographics:
                return {
                    "success": False,
                    "error": f"No patient found with DFN {patient_dfn}",
                    "metadata": build_metadata(
                        station=station, rpc_name="ORWPT ID INFO"
                    ),
                }

            # Set station
            demographics.station = station

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="ORWPT ID INFO",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            return {
                "success": True,
                "patient": demographics.model_dump(),
                "metadata": build_metadata(
                    station=station,
                    rpc_name="ORWPT ID INFO",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWPT ID INFO",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="ORWPT ID INFO"),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_demographics")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="ORWPT ID INFO"),
            }

    @mcp.tool()
    async def select_patient(
        patient_dfn: str,
        station: str | None = None,
    ) -> dict[str, Any]:
        """
        Set the current patient context

        Args:
            patient_dfn: Patient's DFN to select
            station: Vista station number (default: configured default)

        Returns:
            Success status
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
                rpc_name="ORWPT SELECT",
                parameters=[{"string": patient_dfn}],
            )

            # Check result (should be "1" for success)
            success = result == "1"

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log call
            log_rpc_call(
                rpc_name="ORWPT SELECT",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=success,
            )

            if success:
                return {
                    "success": True,
                    "patient_dfn": patient_dfn,
                    "message": f"Patient {patient_dfn} selected successfully",
                    "metadata": build_metadata(
                        station=station,
                        rpc_name="ORWPT SELECT",
                        duration_ms=duration_ms,
                    ),
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to select patient {patient_dfn}",
                    "metadata": build_metadata(
                        station=station, rpc_name="ORWPT SELECT"
                    ),
                }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="ORWPT SELECT",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(station=station, rpc_name="ORWPT SELECT"),
            }

        except Exception as e:
            logger.exception("Unexpected error in select_patient")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(station=station, rpc_name="ORWPT SELECT"),
            }

    @mcp.tool()
    async def get_patient_data(
        patient_dfn: str,
        domains: list[str],
        station: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive patient data from VPR (Virtual Patient Record)

        Args:
            patient_dfn: Patient's DFN
            domains: List of data domains to retrieve (e.g., ["med", "lab", "vital"])
                     Valid domains: patient, allergy, med, lab, vital, problem,
                     appointment, document, procedure, consult, order, visit,
                     surgery, image, immunization, education, exam, factor
            station: Vista station number (default: configured default)
            start_date: Optional start date for data range
            end_date: Optional end date for data range

        Returns:
            Comprehensive patient data in JSON format
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

        # Validate domains
        valid_domains = [d.value for d in VprDomain]
        invalid_domains = [d for d in domains if d not in valid_domains]
        if invalid_domains:
            return {
                "success": False,
                "error": f"Invalid domains: {invalid_domains}. Valid domains: {valid_domains}",
                "metadata": build_metadata(station=station),
            }

        try:
            # Build parameters
            parameters = [
                {"string": patient_dfn},
                {"string": start_date or ""},  # Empty for all dates
                {"string": end_date or ""},
                {"string": ";".join(domains)},  # Semicolon-separated domains
            ]

            # Invoke RPC
            result = await vista_client.invoke_rpc(
                station=station,
                caller_duz=caller_duz,
                rpc_name="VPR GET PATIENT DATA JSON",
                context="VPR APPLICATION PROXY",
                parameters=parameters,
                json_result=True,  # Request JSON response
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Log successful call
            log_rpc_call(
                rpc_name="VPR GET PATIENT DATA JSON",
                station=station,
                duz=caller_duz,
                duration_ms=duration_ms,
                success=True,
            )

            # Build response
            return {
                "success": True,
                "patient_dfn": patient_dfn,
                "domains_requested": domains,
                "data": result,
                "metadata": build_metadata(
                    station=station,
                    rpc_name="VPR GET PATIENT DATA JSON",
                    duration_ms=duration_ms,
                ),
            }

        except VistaAPIError as e:
            log_rpc_call(
                rpc_name="VPR GET PATIENT DATA JSON",
                station=station,
                duz=caller_duz,
                success=False,
                error=str(e),
            )
            return {
                "success": False,
                "error": translate_vista_error(e.to_dict()),
                "metadata": build_metadata(
                    station=station, rpc_name="VPR GET PATIENT DATA JSON"
                ),
            }

        except Exception as e:
            logger.exception("Unexpected error in get_patient_data")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "metadata": build_metadata(
                    station=station, rpc_name="VPR GET PATIENT DATA JSON"
                ),
            }
