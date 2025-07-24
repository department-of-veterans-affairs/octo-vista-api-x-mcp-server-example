"""Centralized mapping system for VistA data parsing

This module provides a centralized way to manage all the various
mappings, dictionaries, and patterns used throughout the parsing system.
"""

from .mapping_loader import MappingLoader

# Global mapping loader instance
_loader = MappingLoader()

# Convenience functions for easy access
get_medication_mappings = _loader.get_medication_mappings
get_clinical_mappings = _loader.get_clinical_mappings
get_frequency_patterns = _loader.get_frequency_patterns
get_status_mappings = _loader.get_status_mappings
normalize_frequency = _loader.normalize_frequency
validate_status = _loader.validate_status
extract_route = _loader.extract_route
extract_timing = _loader.extract_timing

__all__ = [
    "MappingLoader",
    "get_medication_mappings",
    "get_clinical_mappings",
    "get_frequency_patterns",
    "get_status_mappings",
    "normalize_frequency",
    "validate_status",
    "extract_route",
    "extract_timing",
]
