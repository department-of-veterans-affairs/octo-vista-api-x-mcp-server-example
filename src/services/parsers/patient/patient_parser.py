"""Patient data parser for VPR JSON

This module parses the raw Patient Record (VPR) JSON response
into structured Pydantic models for easier consumption.
"""

import logging
from typing import Any

from ....models.patient import (
    Consult,
    LabResult,
    PatientAddress,
    PatientDataCollection,
    PatientDemographics,
    PatientFlag,
    PatientSupport,
    PatientTelecom,
    VeteranInfo,
    VitalSign,
)

logger = logging.getLogger(__name__)


class PatientDataParser:
    """Parser for VPR GET PATIENT DATA JSON response"""

    def __init__(self, station: str, dfn: str):
        """
        Initialize parser with patient identifiers.

        Args:
            station: Station number
            dfn: Patient DFN
        """
        self.station = station
        self.dfn = dfn

    def parse(self, vpr_data: dict[str, Any]) -> PatientDataCollection:
        """
        Parse VPR JSON into structured patient data collection.

        Args:
            vpr_data: Raw VPR JSON response

        Returns:
            PatientDataCollection with parsed data

        Raises:
            ValueError: If required data is missing
        """
        if not vpr_data:
            raise ValueError("VPR data is empty")

        # Handle both wrapped (actual Vista API) and unwrapped (mock) formats
        if "payload" in vpr_data and isinstance(vpr_data["payload"], dict):
            vpr_data = vpr_data["payload"]

        # Get items array
        items = vpr_data.get("data", {}).get("items", [])
        if not items:
            raise ValueError("No items found in VPR data")

        # Group items by type
        grouped = self._group_items_by_type(items)

        # Parse demographics (required)
        demographics = self._parse_demographics(grouped.get("patient", []))
        if not demographics:
            raise ValueError("Patient demographics not found in VPR data")

        # Parse clinical data
        vital_signs = self._parse_vital_signs(grouped.get("vital", []))
        lab_results = self._parse_lab_results(grouped.get("lab", []))
        consults = self._parse_consults(grouped.get("consult", []))

        # Create collection
        collection = PatientDataCollection(
            demographics=demographics,
            vital_signs=vital_signs,
            lab_results=lab_results,
            consults=consults,
            source_station=self.station,
            source_dfn=self.dfn,
            total_items=len(items),
            raw_data=vpr_data,  # Store for debugging
        )

        logger.info(
            f"Parsed patient data for {collection.patient_name}: "
            f"{len(vital_signs)} vitals, {len(lab_results)} labs, "
            f"{len(consults)} consults"
        )

        return collection

    def _group_items_by_type(
        self, items: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group VPR items by their UID type"""
        grouped: dict[str, list[dict[str, Any]]] = {}

        for item in items:
            uid = item.get("uid", "")
            if not uid:
                continue

            # Extract type from UID (e.g., "urn:va:vital:500:12345:33333" -> "vital")
            parts = uid.split(":")
            if len(parts) >= 3:
                item_type = parts[2]  # Third part is the type (urn:va:TYPE:...)
                if item_type not in grouped:
                    grouped[item_type] = []
                grouped[item_type].append(item)

        return grouped

    def _parse_demographics(
        self, patient_items: list[dict[str, Any]]
    ) -> PatientDemographics | None:
        """Parse patient demographics from patient items"""
        if not patient_items:
            return None

        # Take first patient item (should only be one)
        patient_data = patient_items[0]

        # Parse addresses
        addresses = []
        if "addresses" in patient_data:
            for addr_data in patient_data["addresses"]:
                try:
                    addresses.append(PatientAddress(**addr_data))
                except Exception as e:
                    logger.warning(f"Failed to parse address: {e}")

        # Parse telecoms
        telecoms = []
        if "telecoms" in patient_data:
            for telecom_data in patient_data["telecoms"]:
                try:
                    telecoms.append(PatientTelecom(**telecom_data))
                except Exception as e:
                    logger.warning(f"Failed to parse telecom: {e}")

        # Parse supports
        supports = []
        if "supports" in patient_data:
            for support_data in patient_data["supports"]:
                try:
                    supports.append(PatientSupport(**support_data))
                except Exception as e:
                    logger.warning(f"Failed to parse support: {e}")

        # Parse veteran info
        veteran = None
        if "veteran" in patient_data:
            try:
                veteran = VeteranInfo(**patient_data["veteran"])
            except Exception as e:
                logger.warning(f"Failed to parse veteran info: {e}")

        # Parse flags
        flags = []
        if "flags" in patient_data:
            for flag_data in patient_data["flags"]:
                try:
                    flags.append(PatientFlag(**flag_data))
                except Exception as e:
                    logger.warning(f"Failed to parse flag: {e}")

        # Build demographics
        try:
            # Create a copy of patient data and remove the lists we've already parsed
            demographics_data = patient_data.copy()
            demographics_data.pop("addresses", None)
            demographics_data.pop("telecoms", None)
            demographics_data.pop("supports", None)
            demographics_data.pop("veteran", None)
            demographics_data.pop("flags", None)

            # Add DFN from parser context
            demographics_data["dfn"] = self.dfn

            demographics = PatientDemographics(
                **demographics_data,
                addresses=addresses,
                telecoms=telecoms,
                supports=supports,
                veteran=veteran,
                flags=flags,
            )
            return demographics
        except Exception as e:
            logger.error(f"Failed to parse demographics: {e}")
            raise

    def _parse_vital_signs(self, vital_items: list[dict[str, Any]]) -> list[VitalSign]:
        """Parse vital signs from vital items"""
        vitals = []

        for item in vital_items:
            try:
                vital = VitalSign(**item)
                vitals.append(vital)
            except Exception as e:
                logger.warning(f"Failed to parse vital sign {item.get('uid')}: {e}")

        # Sort by observed date (newest first)
        vitals.sort(key=lambda v: v.observed, reverse=True)

        return vitals

    def _parse_lab_results(self, lab_items: list[dict[str, Any]]) -> list[LabResult]:
        """Parse lab results from lab items"""
        labs = []

        for item in lab_items:
            try:
                lab = LabResult(**item)
                labs.append(lab)
            except Exception as e:
                logger.warning(f"Failed to parse lab result {item.get('uid')}: {e}")

        # Sort by observed date (newest first)
        labs.sort(key=lambda lab: lab.observed, reverse=True)

        return labs

    def _parse_consults(self, consult_items: list[dict[str, Any]]) -> list[Consult]:
        """Parse consultations from consult items"""
        consults = []

        for item in consult_items:
            try:
                consult = Consult(**item)
                consults.append(consult)
            except Exception as e:
                logger.warning(f"Failed to parse consult {item.get('uid')}: {e}")

        # Sort by date (newest first)
        consults.sort(key=lambda c: c.date_time, reverse=True)

        return consults


def parse_vpr_patient_data(
    vpr_json: dict[str, Any], station: str, dfn: str
) -> PatientDataCollection:
    """
    Convenience function to parse VPR patient data.

    Args:
        vpr_json: Raw VPR JSON response
        station: VistA station number
        dfn: Patient DFN

    Returns:
        Parsed PatientDataCollection
    """
    parser = PatientDataParser(station, dfn)
    return parser.parse(vpr_json)
