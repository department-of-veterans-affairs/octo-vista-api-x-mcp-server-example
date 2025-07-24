"""Tests for the centralized mapping system"""

import pytest

from src.services.parsers.mappings import (
    MappingLoader,
    extract_route,
    extract_timing,
    get_clinical_mappings,
    get_medication_mappings,
    normalize_frequency,
    validate_status,
)


class TestMappingLoader:
    """Test the MappingLoader class directly"""

    def test_singleton_behavior(self):
        """Test that the mapping loader behaves like a singleton"""
        loader1 = MappingLoader()
        loader2 = MappingLoader()

        # Should load the same data
        mappings1 = loader1.get_medication_mappings()
        mappings2 = loader2.get_medication_mappings()

        assert mappings1 == mappings2

    def test_load_medication_mappings(self):
        """Test loading medication mappings"""
        loader = MappingLoader()
        mappings = loader.get_medication_mappings()

        # Check required sections exist
        assert "frequency_extraction_patterns" in mappings
        assert "frequency_normalization" in mappings
        assert "status_mappings" in mappings
        assert "route_patterns" in mappings
        assert "timing_patterns" in mappings
        assert "medication_forms" in mappings

    def test_load_clinical_mappings(self):
        """Test loading clinical mappings"""
        loader = MappingLoader()
        mappings = loader.get_clinical_mappings()

        # Check required sections exist
        assert "specimen_types" in mappings
        assert "vital_sign_types" in mappings
        assert "abnormal_flags" in mappings
        assert "consult_status_mappings" in mappings


class TestConvenienceFunctions:
    """Test the convenience functions from __init__.py"""

    def test_get_medication_mappings(self):
        """Test getting medication mappings"""
        mappings = get_medication_mappings()
        assert "frequency_normalization" in mappings
        assert "BID" in mappings["frequency_normalization"]

    def test_get_clinical_mappings(self):
        """Test getting clinical mappings"""
        mappings = get_clinical_mappings()
        assert "abnormal_flags" in mappings
        assert "H" in mappings["abnormal_flags"]

    def test_normalize_frequency(self):
        """Test frequency normalization"""
        assert normalize_frequency("BID") == "twice daily"
        assert normalize_frequency("TID") == "three times daily"
        assert normalize_frequency("PRN") == "as needed"
        assert normalize_frequency("") == "as directed"

    def test_validate_status(self):
        """Test status validation"""
        assert validate_status("A", "medication") == "ACTIVE"
        assert validate_status("D", "medication") == "DISCONTINUED"
        assert validate_status("STOPPED", "medication") == "DISCONTINUED"
        assert validate_status("", "medication") == "ACTIVE"

    def test_extract_route(self):
        """Test route extraction"""
        assert extract_route("TAKE 1 TABLET BY MOUTH DAILY") == "PO"
        assert extract_route("INJECT 10 UNITS SUBCUTANEOUS") == "SQ"
        assert extract_route("APPLY TO AFFECTED AREA") == "TOP"
        assert extract_route("NO ROUTE SPECIFIED") is None

    def test_extract_timing(self):
        """Test timing extraction"""
        assert extract_timing("TAKE WITH MEALS") == "with meals"
        assert extract_timing("TAKE AT BEDTIME") == "at bedtime"
        assert extract_timing("TAKE IN THE MORNING") == "in morning"
        assert extract_timing("NO TIMING SPECIFIED") is None


class TestFrequencyPatterns:
    """Test frequency extraction and normalization patterns"""

    def test_frequency_extraction_from_sig(self):
        """Test extracting frequency codes from SIG instructions"""
        loader = MappingLoader()

        assert loader.extract_frequency_from_sig("TAKE TWICE DAILY") == "BID"
        assert loader.extract_frequency_from_sig("TAKE ONCE DAILY") == "QD"
        assert loader.extract_frequency_from_sig("TAKE THREE TIMES DAILY") == "TID"
        assert loader.extract_frequency_from_sig("TAKE AS NEEDED") == "PRN"

    def test_complex_frequency_normalization(self):
        """Test complex frequency pattern normalization"""
        # Test "EVERY X HOURS" pattern
        assert normalize_frequency("EVERY 12 HOURS") == "twice daily"
        assert normalize_frequency("EVERY 8 HOURS") == "three times daily"

        # Test "X TIMES A DAY" pattern
        assert normalize_frequency("2 TIMES A DAY") == "twice daily"
        assert normalize_frequency("3 TIMES PER DAY") == "three times daily"

        # Test "X TIMES WEEKLY" pattern
        assert normalize_frequency("2 TIMES WEEKLY") == "twice weekly"


class TestSpecialInstructions:
    """Test special instruction extraction"""

    def test_extract_special_instructions(self):
        """Test extracting special instructions from SIG"""
        loader = MappingLoader()

        instructions1 = loader.extract_special_instructions("TAKE AS NEEDED FOR PAIN")
        assert instructions1.get("as_needed") is True

        instructions2 = loader.extract_special_instructions(
            "SWALLOW WHOLE, DO NOT CRUSH"
        )
        assert instructions2.get("do_not_crush") is True

        instructions3 = loader.extract_special_instructions("TAKE WITH PLENTY OF WATER")
        assert instructions3.get("with_water") is True


class TestClinicalMappings:
    """Test clinical data mappings"""

    def test_specimen_type_cleaning(self):
        """Test specimen type cleaning and mapping"""
        loader = MappingLoader()

        assert loader.clean_specimen_type("SER") == "SERUM"
        assert loader.clean_specimen_type("PLM") == "PLASMA"
        assert loader.clean_specimen_type("WHOLE BLOOD") == "WHOLE BLOOD"
        assert loader.clean_specimen_type("") is None
        assert loader.clean_specimen_type("N/A") is None

    def test_abnormal_flag_meanings(self):
        """Test abnormal flag meanings"""
        loader = MappingLoader()

        assert loader.get_abnormal_flag_meaning("H") == "HIGH"
        assert loader.get_abnormal_flag_meaning("L") == "LOW"
        assert loader.get_abnormal_flag_meaning("*H") == "CRITICALLY HIGH"
        assert loader.get_abnormal_flag_meaning("") is None

    def test_consult_status_mappings(self):
        """Test consult status mappings"""
        assert validate_status("P", "consult") == "PENDING"
        assert validate_status("S", "consult") == "SCHEDULED"
        assert validate_status("A", "consult") == "ACTIVE"
        assert validate_status("C", "consult") == "COMPLETED"


class TestErrorHandling:
    """Test error handling in mapping system"""

    def test_unknown_mapping_type(self):
        """Test handling of unknown mapping types"""
        loader = MappingLoader()

        with pytest.raises(ValueError, match="Unknown mapping type"):
            loader.get_status_mappings("unknown_type")

    def test_missing_values_handled_gracefully(self):
        """Test that missing values are handled gracefully"""
        # These should not raise exceptions
        assert normalize_frequency(None) == "as directed"
        assert validate_status(None, "medication") == "ACTIVE"
        assert extract_route(None) is None
        assert extract_timing(None) is None


class TestBackwardCompatibility:
    """Test that the centralized system maintains backward compatibility"""

    def test_medication_forms_available(self):
        """Test that medication forms are available"""
        loader = MappingLoader()
        forms = loader.get_medication_forms()

        # Check some expected forms
        assert "TAB" in forms
        assert "TABLET" in forms
        assert "CAP" in forms
        assert "CAPSULE" in forms
        assert "SYRUP" in forms

    def test_all_original_patterns_preserved(self):
        """Test that all original functionality is preserved"""
        # These were all working in the original value_parser.py
        assert normalize_frequency("BID") == "twice daily"
        assert normalize_frequency("Q12H") == "twice daily"
        assert normalize_frequency("TWICE DAILY") == "twice daily"

        assert validate_status("A", "medication") == "ACTIVE"
        assert validate_status("ACTIVE", "medication") == "ACTIVE"
        assert validate_status("DISCONTINUED", "medication") == "DISCONTINUED"

        assert extract_route("BY MOUTH") == "PO"
        assert extract_route("SUBCUTANEOUS") == "SQ"
        assert extract_route("INJECTION") == "IM"
