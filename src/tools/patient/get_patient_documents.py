"""Get patient documents tool for MCP server"""

from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

from ...services.data import get_patient_data
from ...services.validators import validate_dfn
from ...utils import build_metadata, get_default_duz, get_default_station, get_logger
from ...vista.base import BaseVistaClient

logger = get_logger()


def register_get_patient_documents_tool(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register the get_patient_documents tool with the MCP server"""

    @mcp.tool()
    async def get_patient_documents(
        patient_dfn: str,
        station: str = "",
        completed_only: bool = True,
        days_back: int = 180,
    ) -> dict:
        """Get patient clinical documents and notes."""
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

            # Filter documents by date
            cutoff_date = datetime.now() - timedelta(days=days_back)
            documents = [
                d
                for d in patient_data.documents
                if d.reference_date_time and d.reference_date_time >= cutoff_date
            ]

            # Filter by completion status if requested
            if completed_only:
                documents = [d for d in documents if d.is_completed]

            # Build response
            return {
                "success": True,
                "patient": {
                    "dfn": patient_dfn,
                    "name": patient_data.patient_name,
                    "age": patient_data.demographics.calculate_age(),
                },
                "documents": {
                    "total": len(documents),
                    "completed": len([d for d in documents if d.is_completed]),
                    "progress_notes": len([d for d in documents if d.is_progress_note]),
                    "consult_notes": len([d for d in documents if d.is_consult_note]),
                    "items": [
                        {
                            "uid": doc.uid,
                            "local_id": doc.local_id,
                            "document_class": doc.document_class,
                            "document_type": doc.document_type_name,
                            "local_title": doc.local_title,
                            "national_title": (
                                doc.national_title.title if doc.national_title else None
                            ),
                            "status": doc.status_name,
                            "completed": doc.is_completed,
                            "entered": doc.entered.isoformat() if doc.entered else None,
                            "reference_date": (
                                doc.reference_date_time.isoformat()
                                if doc.reference_date_time
                                else None
                            ),
                            "encounter_name": doc.encounter_name,
                            "facility": {
                                "code": doc.facility_code,
                                "name": doc.facility_name,
                            },
                            "author": doc.primary_author,
                            "has_signature": doc.has_signature,
                            "content_summary": doc.content_summary,
                            "text_items": len(doc.text),
                        }
                        for doc in documents
                    ],
                },
                "metadata": build_metadata(station=station),
            }

        except Exception as e:
            logger.error(f"Error getting patient documents: {e}")
            return {
                "success": False,
                "error": f"Failed to retrieve patient documents: {str(e)}",
                "metadata": build_metadata(station=station),
            }
