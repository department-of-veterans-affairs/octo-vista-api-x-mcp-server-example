"""Data access services that handle caching transparently."""

from .patient_data import get_patient_data

__all__ = [
    "get_patient_data",
]
