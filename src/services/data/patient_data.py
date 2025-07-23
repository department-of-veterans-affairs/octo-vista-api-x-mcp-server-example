"""Patient data access service with transparent caching."""

from ...models.patient.patient import PatientDataCollection
from ...services.cache.factory import CacheFactory
from ...services.parsers.patient.patient_parser import parse_vpr_patient_data
from ...services.rpc import build_named_array_param, execute_rpc
from ...vista.base import BaseVistaClient, VistaAPIError

# Module-level cache instance
_cache_instance = None


async def _get_cache():
    """Get or create singleton cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = await CacheFactory.create_patient_cache()
    return _cache_instance


async def get_patient_data(
    vista_client: BaseVistaClient,
    station: str,
    patient_dfn: str,
    caller_duz: str,
) -> PatientDataCollection:
    """Get patient data with transparent caching.

    This function handles all caching logic internally. It will:
    1. Check the cache for existing data
    2. If not found, fetch from VistA
    3. Parse and cache the results
    4. Return the patient data collection

    Args:
        vista_client: The Vista API client
        station: Station ID
        patient_dfn: Patient DFN
        caller_duz: Caller DUZ

    Returns:
        PatientDataCollection with all patient data

    Raises:
        VistaAPIError: If the RPC call fails
    """
    # Get cache instance
    cache = await _get_cache()

    # Check cache first
    cached_data = await cache.get_patient_data(station, patient_dfn, caller_duz)

    if cached_data:
        # Return cached data
        return PatientDataCollection(**cached_data)

    # Fetch from VistA using RPC executor
    rpc_result = await execute_rpc(
        vista_client=vista_client,
        rpc_name="VPR GET PATIENT DATA JSON",
        parameters=build_named_array_param({"patientId": patient_dfn}),
        parser=lambda result: parse_vpr_patient_data(result, station, patient_dfn),
        station=station,
        caller_duz=caller_duz,
        context="LHS RPC CONTEXT",
        json_result=True,
        error_response_builder=lambda error, metadata: {
            "error": error,
            "metadata": metadata,
        },
    )

    # Check if this is an error response
    if "error" in rpc_result:
        raise VistaAPIError(
            error_type="RPC_ERROR",
            error_code="RPC_FAILED",
            message=rpc_result["error"],
            status_code=500,
        )

    # Get parsed data
    patient_data = rpc_result["parsed_data"]

    # Cache for next time
    await cache.set_patient_data(
        station, patient_dfn, caller_duz, patient_data.model_dump()
    )

    return patient_data
