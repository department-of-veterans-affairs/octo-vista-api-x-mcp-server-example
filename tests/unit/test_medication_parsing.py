"""Tests for medication parsing utilities"""

from datetime import UTC, datetime, timedelta

from src.models.patient.medication import Medication
from src.services.parsers.patient.value_parser import (
    extract_medication_instructions,
    normalize_medication_frequency,
    parse_medication_dosage,
    validate_medication_status,
)


class TestMedicationParsing:
    """Test medication parsing functions"""

    def test_parse_medication_dosage_simple(self):
        """Test parsing simple dosage formats"""
        strength, unit, form = parse_medication_dosage("500MG TAB")
        assert strength == "500"
        assert unit == "MG"
        assert form == "TAB"

    def test_parse_medication_dosage_complex(self):
        """Test parsing complex dosage formats"""
        strength, unit, form = parse_medication_dosage("10MG/5ML SYRUP")
        assert strength == "10/5"
        assert unit == "MG/ML"
        assert form == "SYRUP"

    def test_parse_medication_dosage_no_form(self):
        """Test parsing dosage without form"""
        strength, unit, form = parse_medication_dosage("INSULIN 100UNITS/ML")
        assert strength == "100"
        assert unit == "UNITS/ML"
        assert form is None

    def test_normalize_medication_frequency_standard(self):
        """Test normalizing standard frequency abbreviations"""
        assert normalize_medication_frequency("BID") == "twice daily"
        assert normalize_medication_frequency("TID") == "three times daily"
        assert normalize_medication_frequency("QD") == "once daily"
        assert normalize_medication_frequency("PRN") == "as needed"

    def test_normalize_medication_frequency_complex(self):
        """Test normalizing complex frequency patterns"""
        assert normalize_medication_frequency("EVERY 8 HOURS") == "three times daily"
        assert normalize_medication_frequency("2 TIMES A DAY") == "twice daily"
        assert normalize_medication_frequency("3 TIMES WEEKLY") == "three times weekly"

    def test_normalize_medication_frequency_empty(self):
        """Test handling empty frequency"""
        assert normalize_medication_frequency("") == "as directed"
        assert normalize_medication_frequency(None) == "as directed"

    def test_validate_medication_status_standard(self):
        """Test validating standard medication statuses"""
        assert validate_medication_status("ACTIVE") == "ACTIVE"
        assert validate_medication_status("DISCONTINUED") == "DISCONTINUED"
        assert validate_medication_status("COMPLETED") == "COMPLETED"

    def test_validate_medication_status_variations(self):
        """Test validating status variations"""
        assert validate_medication_status("A") == "ACTIVE"
        assert validate_medication_status("D") == "DISCONTINUED"
        assert validate_medication_status("STOPPED") == "DISCONTINUED"
        assert validate_medication_status("EXPIRED") == "DISCONTINUED"
        assert validate_medication_status("") == "ACTIVE"

    def test_extract_medication_instructions_route(self):
        """Test extracting route from SIG instructions"""
        instructions = extract_medication_instructions("TAKE 1 TABLET BY MOUTH DAILY")
        assert instructions.get("route") == "PO"

        instructions = extract_medication_instructions("INJECT 10 UNITS SUBCUTANEOUS")
        assert instructions.get("route") == "SQ"

    def test_extract_medication_instructions_timing(self):
        """Test extracting timing from SIG instructions"""
        instructions = extract_medication_instructions("TAKE WITH MEALS")
        assert instructions.get("timing") == "with meals"

        instructions = extract_medication_instructions("TAKE AT BEDTIME")
        assert instructions.get("timing") == "at bedtime"

    def test_extract_medication_instructions_special(self):
        """Test extracting special instructions"""
        instructions = extract_medication_instructions("TAKE AS NEEDED FOR PAIN")
        assert instructions.get("as_needed") is True

        instructions = extract_medication_instructions("SWALLOW WHOLE, DO NOT CRUSH")
        assert instructions.get("do_not_crush") is True


class TestMedicationModel:
    """Test Medication model functionality"""

    def test_medication_creation_basic(self):
        """Test creating a basic medication instance"""
        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "productFormName": "METFORMIN 1000MG TAB",
            "dosageForm": "TABLET",
            "sig": "TAKE 1 TABLET BY MOUTH TWICE DAILY",
            "overallStart": 20240101,
            "vaStatus": "ACTIVE",
            "facilityCode": 500,
            "facilityName": "TEST FACILITY",
        }

        medication = Medication(**med_data)

        assert medication.medication_name == "METFORMIN 1000MG TAB"
        assert medication.dosage == "TABLET"
        assert medication.sig == "TAKE 1 TABLET BY MOUTH TWICE DAILY"
        assert medication.status == "ACTIVE"
        assert medication.is_active is True
        assert medication.is_discontinued is False

    def test_medication_display_properties(self):
        """Test medication display properties"""
        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "productFormName": "LISINOPRIL 20MG TAB",  # Include strength in name
            "dosageForm": "TABLET",
            "sig": "TAKE 1 TABLET BY MOUTH TWICE DAILY",
            "overallStart": 20240101,
            "vaStatus": "ACTIVE",
            "facilityCode": 500,
            "facilityName": "TEST FACILITY",
        }

        medication = Medication(**med_data)

        # Should extract strength from medication name
        assert medication.strength == "20MG"  # Should be extracted
        assert "20MG" in medication.display_name

        # Frequency should be extracted from SIG
        assert medication.display_frequency == "twice daily"

    def test_medication_refill_logic(self):
        """Test medication refill calculation logic"""
        # Create a medication filled 85 days ago with 90 days supply (closer to needing refill)
        last_filled = datetime.now(UTC) - timedelta(days=85)

        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "productFormName": "ASPIRIN 81MG TAB",
            "dosageForm": "TABLET",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "overallStart": 20240101,
            "lastFilled": int(last_filled.strftime("%Y%m%d")),
            "daysSupply": 90,
            "vaStatus": "ACTIVE",
            "facilityCode": 500,
            "facilityName": "TEST FACILITY",
        }

        medication = Medication(**med_data)

        # Should need refill soon (within 7 days)
        days_until_refill = medication.days_until_refill_needed
        assert days_until_refill is not None
        assert days_until_refill <= 7  # Should be close to needing refill
        assert medication.needs_refill_soon is True

    def test_medication_discontinued_status(self):
        """Test discontinued medication handling"""
        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "productFormName": "WARFARIN 5MG TAB",
            "dosageForm": "TABLET",
            "sig": "TAKE AS DIRECTED",
            "overallStart": 20231201,
            "overallStop": 20240301,
            "vaStatus": "DISCONTINUED",
            "facilityCode": 500,
            "facilityName": "TEST FACILITY",
        }

        medication = Medication(**med_data)

        assert medication.is_active is False
        assert medication.is_discontinued is True
        assert medication.status == "DISCONTINUED"

    def test_medication_sig_parsing(self):
        """Test SIG instruction parsing"""
        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "productFormName": "GABAPENTIN 300MG CAP",
            "dosageForm": "CAPSULE",
            "sig": "TAKE 1 CAPSULE BY MOUTH THREE TIMES DAILY WITH FOOD",
            "overallStart": 20240101,
            "vaStatus": "ACTIVE",
            "facilityCode": 500,
            "facilityName": "TEST FACILITY",
        }

        medication = Medication(**med_data)

        # Should extract frequency and route from SIG
        assert medication.frequency == "TID"
        assert medication.route == "PO"
        assert medication.display_frequency == "three times daily"

    def test_medication_strength_extraction(self):
        """Test strength extraction from medication name"""
        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "productFormName": "SERTRALINE 100MG TAB",
            "dosageForm": "TABLET",
            "sig": "TAKE 1 TABLET DAILY",
            "overallStart": 20240101,
            "vaStatus": "ACTIVE",
            "facilityCode": 500,
            "facilityName": "TEST FACILITY",
        }

        medication = Medication(**med_data)

        # Should extract strength from name
        assert medication.strength == "100MG"
        assert "100MG" in medication.display_name

    def test_medication_with_nested_orders(self):
        """Test medication with orders array for prescriber info"""
        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "productFormName": "METFORMIN 500MG TAB",
            "dosageForm": "TABLET",
            "sig": "TAKE 1 TABLET TWICE DAILY",
            "overallStart": 20240101,
            "vaStatus": "ACTIVE",
            "facilityCode": 500,
            "facilityName": "TEST FACILITY",
            "orders": [
                {
                    "providerName": "SMITH,JOHN MD",
                    "providerUid": "urn:va:user:500:12345",
                }
            ],
        }

        # Need to preprocess like the parser would
        from src.services.parsers.patient.patient_parser import PatientDataParser

        parser = PatientDataParser("500", "123")
        processed_data = parser._preprocess_medication_item(med_data)

        medication = Medication(**processed_data)

        assert medication.prescriber == "SMITH,JOHN MD"
        assert medication.prescriber_uid == "urn:va:user:500:12345"
