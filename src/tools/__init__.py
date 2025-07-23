"""Vista API MCP Tools"""

from .patient import register_patient_tools
from .system import register_system_tools

__all__ = [
    "register_patient_tools",
    "register_system_tools",
]
