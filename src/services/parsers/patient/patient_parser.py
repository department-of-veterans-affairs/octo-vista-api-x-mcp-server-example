"""Patient data parser for VPR JSON

This module parses the raw Patient Record (VPR) JSON response
into structured Pydantic models for easier consumption.
"""

from datetime import datetime
from typing import Any

from jsonpath_ng import parse as jsonpath_parse  # type: ignore

from ....models.patient import (
    Consult,
    CPTCode,
    Diagnosis,
    Document,
    HealthFactor,
    LabResult,
    Medication,
    Order,
    PatientAddress,
    PatientDataCollection,
    PatientDemographics,
    PatientFlag,
    PatientSupport,
    PatientTelecom,
    VeteranInfo,
    Visit,
    VitalSign,
)
from ....utils import get_logger

logger = get_logger()


class PatientDataParser:
    """Parser for VPR GET PATIENT DATA JSON response using JSONPath"""

    def __init__(self, station: str, dfn: str):
        """
        Initialize parser with patient identifiers.

        Args:
            station: Station number
            dfn: Patient DFN
        """
        self.station = station
        self.dfn = dfn

        # Pre-compile JSONPath expressions for better performance
        self._jsonpath_expressions = {
            # Core data extraction
            "items": jsonpath_parse("$.data.items[*]"),
            "payload_items": jsonpath_parse("$.payload.data.items[*]"),
            # Patient demographics
            "patient_addresses": jsonpath_parse("$.addresses[*]"),
            "patient_telecoms": jsonpath_parse("$.telecoms[*]"),
            "patient_supports": jsonpath_parse("$.supports[*]"),
            "patient_veteran": jsonpath_parse("$.veteran"),
            "patient_flags": jsonpath_parse("$.flags[*]"),
            # Medication specific
            "med_orders": jsonpath_parse("$.orders[*]"),
            "med_prescriber": jsonpath_parse("$.orders[0].providerName"),
            "med_prescriber_uid": jsonpath_parse("$.orders[0].providerUid"),
        }

    def parse(self, vpr_data: dict[str, Any]) -> PatientDataCollection:
        """
        Parse VPR JSON into structured patient data collection using JSONPath.

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

        # Get items using JSONPath
        items = self._extract_items(vpr_data)
        if not items:
            raise ValueError("No items found in VPR data")

        # Group items by type using UID pattern matching
        grouped_items = self._group_items_by_uid_type(items)

        # Parse demographics (required)
        demographics = self._parse_demographics(grouped_items.get("patient", []))
        if not demographics:
            raise ValueError("Patient demographics not found in VPR data")

        # Parse clinical data
        vital_signs = self._parse_vital_signs(grouped_items.get("vital", []))
        lab_results = self._parse_lab_results(grouped_items.get("lab", []))
        consults = self._parse_consults(grouped_items.get("consult", []))
        medications = self._parse_medications(grouped_items.get("med", []))
        visits = self._parse_visits(grouped_items.get("visit", []))
        health_factors = self._parse_health_factors(grouped_items.get("factor", []))
        orders = self._parse_orders(grouped_items.get("order", []))
        documents = self._parse_documents(grouped_items.get("document", []))
        cpt_codes = self._parse_cpt_codes(grouped_items.get("cpt", []))

        problem_items = grouped_items.get("problem", [])
        pov_items = grouped_items.get("pov", [])
        all_diagnosis_items = problem_items + pov_items
        diagnoses = self._parse_diagnoses(all_diagnosis_items)

        # Create collection
        collection = PatientDataCollection(
            demographics=demographics,
            vital_signs=vital_signs,
            lab_results=lab_results,
            consults=consults,
            medications=medications,
            visits=visits,
            health_factors=health_factors,
            diagnoses=diagnoses,
            orders=orders,
            documents=documents,
            cpt_codes=cpt_codes,
            source_station=self.station,
            source_dfn=self.dfn,
            total_items=len(items),
            raw_data=vpr_data,  # Store for debugging
        )

        logger.info(
            f"Parsed patient data for {collection.patient_name}: "
            f"{len(vital_signs)} vitals, {len(lab_results)} labs, "
            f"{len(consults)} consults, {len(medications)} medications, "
            f"{len(visits)} visits, {len(health_factors)} health factors, "
            f"{len(diagnoses)} diagnoses, {len(orders)} orders, "
            f"{len(documents)} documents, {len(cpt_codes)} CPT codes"
        )

        return collection

    def _extract_items(self, vpr_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract items from VPR data using JSONPath"""
        # Try standard format first
        items_matches = self._jsonpath_expressions["items"].find(vpr_data)
        if items_matches:
            return [match.value for match in items_matches]

        # Try payload format
        payload_matches = self._jsonpath_expressions["payload_items"].find(vpr_data)
        if payload_matches:
            return [match.value for match in payload_matches]

        return []

    def _group_items_by_uid_type(
        self, items: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group VPR items by their UID type using Python filtering"""
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
        """Parse patient demographics from patient items using JSONPath"""
        if not patient_items:
            return None

        # Take first patient item (should only be one)
        patient_data = patient_items[0]

        # Parse addresses using JSONPath
        addresses = []
        address_matches = self._jsonpath_expressions["patient_addresses"].find(
            patient_data
        )
        for match in address_matches:
            try:
                addresses.append(PatientAddress(**match.value))
            except Exception as e:
                logger.warning(f"Failed to parse address: {e}")

        # Parse telecoms using JSONPath
        telecoms = []
        telecom_matches = self._jsonpath_expressions["patient_telecoms"].find(
            patient_data
        )
        for match in telecom_matches:
            try:
                telecoms.append(PatientTelecom(**match.value))
            except Exception as e:
                logger.warning(f"Failed to parse telecom: {e}")

        # Parse supports using JSONPath
        supports = []
        support_matches = self._jsonpath_expressions["patient_supports"].find(
            patient_data
        )
        for match in support_matches:
            try:
                supports.append(PatientSupport(**match.value))
            except Exception as e:
                logger.warning(f"Failed to parse support: {e}")

        # Parse veteran info using JSONPath
        veteran = None
        veteran_matches = self._jsonpath_expressions["patient_veteran"].find(
            patient_data
        )
        if veteran_matches:
            try:
                veteran = VeteranInfo(**veteran_matches[0].value)
            except Exception as e:
                logger.warning(f"Failed to parse veteran info: {e}")

        # Parse flags using JSONPath
        flags = []
        flag_matches = self._jsonpath_expressions["patient_flags"].find(patient_data)
        for match in flag_matches:
            try:
                flags.append(PatientFlag(**match.value))
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

    def _parse_medications(self, med_items: list[dict[str, Any]]) -> list[Medication]:
        """Parse medications from med items"""
        medications = []

        for item in med_items:
            try:
                # Preprocess the medication data
                processed_item = self._preprocess_medication_item(item)
                medication = Medication(**processed_item)
                medications.append(medication)
            except Exception as e:
                logger.warning(f"Failed to parse medication {item.get('uid')}: {e}")
                logger.debug(f"Medication item data: {item}")

        # Sort by start date (newest first), handling None dates
        medications.sort(key=lambda m: m.start_date or datetime.min, reverse=True)

        return medications

    def _parse_visits(self, visit_items: list[dict[str, Any]]) -> list[Visit]:
        """Parse visits from visit items"""
        visits = []

        for item in visit_items:
            try:
                # Pre-process visit data
                processed_item = self._preprocess_visit_item(item)
                visit = Visit(**processed_item)
                visits.append(visit)
            except Exception as e:
                logger.warning(f"Failed to parse visit {item.get('uid')}: {e}")
                logger.debug(f"Visit item data: {item}")

        # Sort by visit date (newest first)
        visits.sort(key=lambda v: v.visit_date, reverse=True)

        return visits

    def _preprocess_medication_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Preprocess medication item using JSONPath for nested field extraction"""
        processed = item.copy()

        # Extract prescriber info using JSONPath
        prescriber_matches = self._jsonpath_expressions["med_prescriber"].find(item)
        if prescriber_matches:
            processed["prescriber"] = prescriber_matches[0].value

        prescriber_uid_matches = self._jsonpath_expressions["med_prescriber_uid"].find(
            item
        )
        if prescriber_uid_matches:
            processed["prescriber_uid"] = prescriber_uid_matches[0].value

        # Handle SIG instructions - can be string or array
        if "sig" in processed:
            sig = processed["sig"]
            if isinstance(sig, list):
                processed["sig"] = " ".join(str(s) for s in sig if s)
            elif not sig:
                processed["sig"] = ""

        # Ensure required fields have defaults
        if "dosageForm" not in processed:
            processed["dosageForm"] = "UNKNOWN"

        if "vaStatus" not in processed:
            processed["vaStatus"] = "ACTIVE"

        # Handle product form name variations
        if "productFormName" not in processed:
            # Try alternative field names using JSONPath
            alternative_fields = ["name", "medicationName", "drugName"]
            for alt_field in alternative_fields:
                alt_expr = jsonpath_parse(f"$.{alt_field}")
                matches = alt_expr.find(processed)
                if matches:
                    processed["productFormName"] = matches[0].value
                    break
            else:
                processed["productFormName"] = "UNKNOWN MEDICATION"

        # Handle missing overallStart (required for start_date)
        if "overallStart" not in processed:
            # Try alternative date fields
            date_alternatives = ["start", "startDate", "prescribedDate", "entered"]
            for alt_field in date_alternatives:
                if alt_field in processed and processed[alt_field]:
                    processed["overallStart"] = processed[alt_field]
                    break
            else:
                # Default to current date if no start date found
                from datetime import datetime

                processed["overallStart"] = datetime.now().strftime("%Y%m%d")

        return processed

    def _parse_health_factors(
        self, factor_items: list[dict[str, Any]]
    ) -> list[HealthFactor]:
        """Parse health factors from factor items"""
        health_factors = []

        for item in factor_items:
            try:
                # Preprocess the health factor data
                processed_item = self._preprocess_health_factor_item(item)

                # Skip malformed items that return None
                if processed_item is None:
                    continue

                health_factor = HealthFactor(**processed_item)
                health_factors.append(health_factor)
            except Exception as e:
                logger.warning(f"Failed to parse health factor {item.get('uid')}: {e}")
                logger.debug(f"Health factor item data: {item}")

        # Sort by recorded date (newest first)
        health_factors.sort(key=lambda f: f.recorded_date, reverse=True)

        return health_factors

    def _preprocess_health_factor_item(
        self, item: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Preprocess health factor item for field normalization"""
        processed = item.copy()

        if (
            "uid" not in processed
            or not processed["uid"]
            or processed.get("invalid") == "data"
        ):
            logger.warning(f"Skipping malformed health factor data: {item}")
            return None

        # Ensure required fields have defaults
        if "name" not in processed:
            processed["name"] = "UNKNOWN HEALTH FACTOR"

        if "categoryName" not in processed:
            processed["categoryName"] = "GENERAL"

        if "facilityCode" not in processed:
            processed["facilityCode"] = "000"

        if "facilityName" not in processed:
            processed["facilityName"] = "UNKNOWN FACILITY"

        if "entered" not in processed:
            # Use current date if no date provided
            processed["entered"] = datetime.now().strftime("%Y%m%d")

        # Handle localId - ensure it's present
        if "localId" not in processed:
            # Extract from UID if possible
            uid = processed.get("uid", "")
            if uid:
                parts = uid.split(":")
                if len(parts) >= 4:
                    processed["localId"] = parts[-1]  # Last part of UID
                else:
                    processed["localId"] = "0"
            else:
                processed["localId"] = "0"

        return processed

    def _parse_diagnoses(self, problem_items: list[dict[str, Any]]) -> list[Diagnosis]:
        """Parse diagnoses from problem items"""
        diagnoses = []

        for item in problem_items:
            try:
                # Preprocess the diagnosis data
                processed_item = self._preprocess_diagnosis_item(item)
                diagnosis = Diagnosis(**processed_item)
                diagnoses.append(diagnosis)
            except Exception as e:
                logger.warning(f"Failed to parse diagnosis {item.get('uid')}: {e}")
                logger.debug(f"Diagnosis item data: {item}")

        # Sort by diagnosis date (newest first)
        diagnoses.sort(key=lambda d: d.diagnosis_date, reverse=True)

        return diagnoses

    def _preprocess_diagnosis_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Preprocess diagnosis item for field normalization"""
        processed = item.copy()

        # Ensure required fields have defaults
        if "icdCode" not in processed:
            processed["icdCode"] = ""

        # Clean malformed ICD codes (remove URN:10D: prefix)
        icd_code = processed.get("icdCode", "")
        if icd_code.startswith("urn:10d:"):
            processed["icdCode"] = icd_code[
                8:
            ]  # Remove "urn:10d:" prefix (8 chars, not 9)
        elif icd_code.startswith("URN:10D:"):
            processed["icdCode"] = icd_code[
                8:
            ]  # Remove "URN:10D:" prefix (8 chars, not 9)

        if "icdName" not in processed:
            # Try to get description from "name" field (common in POV data)
            if "name" in processed:
                processed["icdName"] = processed["name"]
            else:
                processed["icdName"] = "UNKNOWN DIAGNOSIS"

        if "facilityCode" not in processed:
            processed["facilityCode"] = "000"

        if "facilityName" not in processed:
            processed["facilityName"] = "UNKNOWN FACILITY"

        if "entered" not in processed:
            # Use current date if no date provided
            from datetime import datetime

            processed["entered"] = datetime.now().strftime("%Y%m%d")

        # Handle localId - ensure it's present
        if "localId" not in processed:
            # Extract from UID if possible
            uid = processed.get("uid", "")
            if uid:
                parts = uid.split(":")
                if len(parts) >= 4:
                    processed["localId"] = parts[-1]  # Last part of UID
                else:
                    processed["localId"] = "0"
            else:
                processed["localId"] = "0"

        # Determine ICD version from code format
        icd_code = processed.get("icdCode", "")
        if icd_code:
            # ICD-10 codes start with letters, ICD-9 codes are numeric
            if any(c.isalpha() for c in icd_code):
                processed["icd_version"] = "ICD-10"
            else:
                processed["icd_version"] = "ICD-9"

        # Set default diagnosis type based on VistA problem type or POV type
        problem_status = processed.get("problemStatus", "").lower()
        pov_type = processed.get("type", "").upper()

        if "primary" in problem_status or pov_type == "P":
            processed["diagnosis_type"] = "primary"
        elif pov_type == "S":
            processed["diagnosis_type"] = "secondary"
        else:
            processed["diagnosis_type"] = "secondary"  # Default

        # Map problem status to diagnosis status
        if problem_status in ["active", "chronic"]:
            processed["status"] = "active"
        elif problem_status in ["resolved", "inactive"]:
            processed["status"] = "resolved"
        else:
            processed["status"] = "active"  # Default

        return processed

    def _parse_orders(self, order_items: list[dict[str, Any]]) -> list[Order]:
        """Parse orders from order items"""
        try:
            parsed = [Order(**order) for order in order_items]
            logger.info(f"Parsed {len(parsed)} orders")
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse orders: {e}")
            return []

    def _parse_documents(self, document_items: list[dict[str, Any]]) -> list[Document]:
        """Parse documents from document items"""
        try:
            # Preprocess each document item
            processed_items = []
            for item in document_items:
                processed = self._preprocess_document_item(item)
                processed_items.append(processed)

            parsed = [Document(**doc) for doc in processed_items]
            logger.info(f"Parsed {len(parsed)} documents")
            return parsed
        except Exception as e:
            logger.warning(f"Failed to parse documents: {e}")
            return []

    def _preprocess_document_item(self, doc_data: dict[str, Any]) -> dict[str, Any]:
        """Preprocess document item before creating Document model"""
        processed = doc_data.copy()

        # Ensure localId is present
        if "localId" not in processed or processed["localId"] is None:
            # Extract from UID if possible
            uid = processed.get("uid", "")
            if uid:
                parts = uid.split(":")
                if len(parts) >= 4:
                    processed["localId"] = parts[-1]  # Last part of UID
                else:
                    processed["localId"] = "0"
            else:
                processed["localId"] = "0"

        return processed

    def _preprocess_visit_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Preprocess visit item data"""
        processed = item.copy()

        # Ensure required fields have defaults
        if "visitDate" not in processed and "admissionDate" in processed:
            processed["visitDate"] = processed["admissionDate"]
        elif "visitDate" not in processed:
            processed["visitDate"] = processed.get("scheduledDate") or processed.get(
                "dateTime"
            )

        if "statusCode" not in processed:
            processed["statusCode"] = "ACTIVE"

        if "statusName" not in processed:
            processed["statusName"] = "ACTIVE"

        # Handle location information
        if "locationCode" not in processed:
            processed["locationCode"] = processed.get("locationId") or "UNKNOWN"

        if "locationName" not in processed:
            processed["locationName"] = processed.get("location") or "UNKNOWN LOCATION"

        # Handle provider information
        if "providerName" not in processed and "attendingProvider" in processed:
            processed["providerName"] = processed["attendingProvider"]

        # Handle facility information
        if "facilityCode" not in processed:
            processed["facilityCode"] = self.station

        if "facilityName" not in processed:
            processed["facilityName"] = "UNKNOWN FACILITY"

        return processed

    def _parse_cpt_codes(self, cpt_items: list[dict[str, Any]]) -> list[CPTCode]:
        """Parse CPT codes from cpt items"""
        cpt_codes = []

        for item in cpt_items:
            try:
                # Preprocess the CPT code data
                processed_item = self._preprocess_cpt_code_item(item)

                # Skip malformed items that return None
                if processed_item is None:
                    continue

                cpt_code = CPTCode(**processed_item)
                cpt_codes.append(cpt_code)
            except Exception as e:
                logger.warning(f"Failed to parse CPT code {item.get('uid')}: {e}")
                logger.debug(f"CPT code item data: {item}")

        # Sort by procedure date (newest first)
        cpt_codes.sort(key=lambda c: c.procedure_date, reverse=True)

        return cpt_codes

    def _preprocess_cpt_code_item(self, item: dict[str, Any]) -> dict[str, Any] | None:
        """Preprocess CPT code item for model creation"""
        if not item:
            return None

        processed = item.copy()

        # Handle required fields
        if "uid" not in processed:
            logger.warning("CPT code item missing UID")
            return None

        # Extract CPT code from URN format if needed
        if "cptCode" in processed:
            cpt_code = processed["cptCode"]
            if isinstance(cpt_code, str) and cpt_code.startswith("urn:cpt:"):
                processed["cptCode"] = cpt_code.split(":")[-1]

        # Set defaults for missing fields
        if "localId" not in processed:
            processed["localId"] = processed.get("uid", "").split(":")[-1]

        if "name" not in processed:
            processed["name"] = ""

        if "dateTime" not in processed:
            # Try to extract from other date fields
            if "performed" in processed:
                processed["dateTime"] = processed["performed"]
            elif "entered" in processed:
                processed["dateTime"] = processed["entered"]
            else:
                logger.warning(
                    f"CPT code item missing dateTime: {processed.get('uid')}"
                )
                return None

        # Ensure facility code and name are present
        if "facilityCode" not in processed:
            processed["facilityCode"] = self.station

        if "facilityName" not in processed:
            processed["facilityName"] = f"Station {self.station}"

        # Handle modifiers if present
        if "modifiers" in processed and isinstance(processed["modifiers"], str):
            from ...validators.cpt_validators import parse_cpt_modifiers

            processed["modifiers"] = parse_cpt_modifiers(processed["modifiers"])

        return processed


def parse_vpr_patient_data(
    vpr_json: dict[str, Any], station: str, dfn: str
) -> PatientDataCollection:
    """
    Convenience function to parse VPR patient data using JSONPath.

    Args:
        vpr_json: Raw VPR JSON response
        station: VistA station number
        dfn: Patient DFN

    Returns:
        Parsed PatientDataCollection
    """
    parser = PatientDataParser(station, dfn)
    return parser.parse(vpr_json)
