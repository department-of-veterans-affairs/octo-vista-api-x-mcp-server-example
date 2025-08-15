"""Patient-related MCP tools coordinator"""

from mcp.server.fastmcp import FastMCP

from ...vista.base import BaseVistaClient
from .get_patient_allergies_tool import register_get_patient_allergies_tool
from .get_patient_consults_tool import register_get_patient_consults_tool
from .get_patient_diagnoses_tool import register_get_patient_diagnoses_tool
from .get_patient_documents import register_get_patient_documents_tool
from .get_patient_health_factors_tool import register_get_patient_health_factors_tool
from .get_patient_labs_tool import register_get_patient_labs_tool
from .get_patient_medications_tool import register_get_patient_medications_tool
from .get_patient_orders import register_get_patient_orders_tool
from .get_patient_povs_tool import register_get_patient_povs_tool
from .get_patient_problems_tool import register_get_patient_problems_tool
from .get_patient_procedures import register_get_patient_procedures_tool
from .get_patient_visits_tool import register_get_patient_visits_tool
from .get_patient_vitals_tool import register_get_patient_vitals_tool


def register_patient_tools(mcp: FastMCP, vista_client: BaseVistaClient):
    """Register all patient-related tools with the MCP server"""

    # Register all individual patient tools
    register_get_patient_vitals_tool(mcp, vista_client)
    register_get_patient_labs_tool(mcp, vista_client)
    register_get_patient_allergies_tool(mcp, vista_client)
    register_get_patient_consults_tool(mcp, vista_client)
    register_get_patient_medications_tool(mcp, vista_client)
    register_get_patient_health_factors_tool(mcp, vista_client)
    register_get_patient_diagnoses_tool(mcp, vista_client)
    register_get_patient_documents_tool(mcp, vista_client)
    register_get_patient_orders_tool(mcp, vista_client)
    register_get_patient_povs_tool(mcp, vista_client)
    register_get_patient_problems_tool(mcp, vista_client)
    register_get_patient_procedures_tool(mcp, vista_client)
    register_get_patient_visits_tool(mcp, vista_client)
