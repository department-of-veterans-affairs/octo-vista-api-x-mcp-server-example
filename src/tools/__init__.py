"""Vista API MCP Tools"""

from .admin import register_admin_tools
from .clinical import register_clinical_tools
from .patient import register_patient_tools
from .system import register_system_tools

__all__ = [
    "register_admin_tools",
    "register_clinical_tools",
    "register_patient_tools",
    "register_system_tools",
]
