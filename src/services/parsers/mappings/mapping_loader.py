"""Mapping loader for centralized parsing mappings"""

import json
import re
from pathlib import Path
from typing import Any


class MappingLoader:
    """Loads and manages centralized mappings for VistA data parsing"""

    def __init__(self):
        """Initialize the mapping loader"""
        self._mappings_dir = Path(__file__).parent
        self._medication_mappings: dict[str, Any] | None = None
        self._clinical_mappings: dict[str, Any] | None = None

    def _load_json_file(self, filename: str) -> dict[str, Any]:
        """Load a JSON mapping file"""
        file_path = self._mappings_dir / filename
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def get_medication_mappings(self) -> dict[str, Any]:
        """Get medication mappings, loading if necessary"""
        if self._medication_mappings is None:
            self._medication_mappings = self._load_json_file("medication_mappings.json")
        return self._medication_mappings

    def get_clinical_mappings(self) -> dict[str, Any]:
        """Get clinical mappings, loading if necessary"""
        if self._clinical_mappings is None:
            self._clinical_mappings = self._load_json_file("clinical_mappings.json")
        return self._clinical_mappings

    def get_frequency_patterns(self) -> dict[str, str]:
        """Get frequency extraction patterns"""
        return self.get_medication_mappings()["frequency_extraction_patterns"]

    def get_status_mappings(self, mapping_type: str = "medication") -> dict[str, str]:
        """
        Get status mappings for a specific type

        Args:
            mapping_type: Type of status mapping ('medication', 'consult', etc.)
        """
        if mapping_type == "medication":
            return self.get_medication_mappings()["status_mappings"]
        elif mapping_type == "consult":
            return self.get_clinical_mappings()["consult_status_mappings"]
        else:
            raise ValueError(f"Unknown mapping type: {mapping_type}")

    def normalize_frequency(self, frequency: str) -> str:
        """
        Normalize medication frequency to standard format using centralized mappings

        Args:
            frequency: Raw frequency string (e.g., "BID", "twice daily", "q12h")

        Returns:
            Normalized frequency string
        """
        if not frequency:
            return "as directed"

        freq_upper = frequency.upper().strip()
        freq_map = self.get_medication_mappings()["frequency_normalization"]

        # Check exact matches first
        if freq_upper in freq_map:
            return freq_map[freq_upper]

        # Pattern matching for complex frequencies
        # "EVERY X HOURS" pattern
        every_hours = re.search(r"EVERY\s+(\d+)\s+HOURS?", freq_upper)
        if every_hours:
            hours = int(every_hours.group(1))
            hours_map = {
                24: "once daily",
                12: "twice daily",
                8: "three times daily",
                6: "four times daily",
            }
            return hours_map.get(hours, f"every {hours} hours")

        # "X TIMES A DAY" pattern
        times_day = re.search(r"(\d+)\s+TIMES?\s+(?:A\s+|PER\s+)?DAY", freq_upper)
        if times_day:
            times = int(times_day.group(1))
            daily_times_map = {
                1: "once daily",
                2: "twice daily",
                3: "three times daily",
                4: "four times daily",
            }
            return daily_times_map.get(times, f"{times} times daily")

        # "X TIMES WEEKLY" pattern
        times_weekly = re.search(r"(\d+)\s+TIMES?\s+(?:A\s+|PER\s+)?WEEK", freq_upper)
        if times_weekly:
            times = int(times_weekly.group(1))
            weekly_times_map = {
                1: "once weekly",
                2: "twice weekly",
                3: "three times weekly",
            }
            return weekly_times_map.get(times, f"{times} times weekly")

        # If no pattern matches, return the original (cleaned up)
        return frequency.lower()

    def validate_status(self, status: str, mapping_type: str = "medication") -> str:
        """
        Validate and normalize status using centralized mappings

        Args:
            status: Raw status string
            mapping_type: Type of status mapping to use

        Returns:
            Normalized status string
        """
        if not status:
            return "ACTIVE" if mapping_type == "medication" else "PENDING"

        status_upper = status.upper().strip()
        status_map = self.get_status_mappings(mapping_type)

        return status_map.get(
            status_upper, "ACTIVE" if mapping_type == "medication" else "PENDING"
        )

    def extract_frequency_from_sig(self, sig: str) -> str | None:
        """
        Extract frequency code from SIG instructions using centralized patterns

        Args:
            sig: SIG instruction string

        Returns:
            Frequency code (e.g., 'BID', 'TID', 'PRN') or None if not found
        """
        if not sig:
            return None

        sig_upper = sig.upper()
        patterns = self.get_frequency_patterns()

        for pattern, freq_code in patterns.items():
            if re.search(pattern, sig_upper):
                return freq_code

        return None

    def extract_route(self, sig: str) -> str | None:
        """
        Extract route from SIG instructions using centralized patterns

        Args:
            sig: SIG instruction string

        Returns:
            Route code (e.g., 'PO', 'IM', 'IV') or None if not found
        """
        if not sig:
            return None

        sig_upper = sig.upper()
        route_patterns = self.get_medication_mappings()["route_patterns"]

        for pattern, route in route_patterns.items():
            if re.search(pattern, sig_upper):
                return route

        return None

    def extract_timing(self, sig: str) -> str | None:
        """
        Extract timing from SIG instructions using centralized patterns

        Args:
            sig: SIG instruction string

        Returns:
            Timing string (e.g., 'with meals', 'at bedtime') or None if not found
        """
        if not sig:
            return None

        sig_upper = sig.upper()
        timing_patterns = self.get_medication_mappings()["timing_patterns"]

        for pattern, timing in timing_patterns.items():
            if re.search(pattern, sig_upper):
                return timing

        return None

    def extract_special_instructions(self, sig: str) -> dict[str, bool]:
        """
        Extract special instructions from SIG using centralized patterns

        Args:
            sig: SIG instruction string

        Returns:
            Dictionary with boolean flags for special instructions
        """
        if not sig:
            return {}

        sig_upper = sig.upper()
        special_patterns = self.get_medication_mappings()[
            "special_instruction_patterns"
        ]
        instructions = {}

        for pattern, instruction_key in special_patterns.items():
            if re.search(pattern, sig_upper):
                instructions[instruction_key] = True

        return instructions

    def get_medication_forms(self) -> list[str]:
        """Get list of medication forms"""
        return self.get_medication_mappings()["medication_forms"]

    def clean_specimen_type(self, specimen: Any) -> str | None:
        """
        Clean and standardize specimen type using centralized mappings

        Args:
            specimen: Raw specimen value from VistA

        Returns:
            Cleaned specimen type or None
        """
        if not specimen:
            return None

        cleaned = str(specimen).strip().upper()
        clinical_mappings = self.get_clinical_mappings()

        # Check if it's an invalid value
        if cleaned in clinical_mappings["specimen_types"]["invalid_values"]:
            return None

        # Check if there's a mapping for the specimen type
        specimen_mappings = clinical_mappings["specimen_types"]["mappings"]
        return specimen_mappings.get(cleaned, cleaned)

    def get_abnormal_flag_meaning(self, flag: str) -> str | None:
        """
        Get the meaning of an abnormal flag

        Args:
            flag: Abnormal flag (e.g., 'H', 'L', '*H')

        Returns:
            Flag meaning or None if not found
        """
        if not flag:
            return None

        abnormal_flags = self.get_clinical_mappings()["abnormal_flags"]
        return abnormal_flags.get(flag.upper(), None)
