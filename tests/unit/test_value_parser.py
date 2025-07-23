"""Tests for value parser"""

from src.services.parsers.patient.value_parser import (
    parse_blood_pressure,
    parse_numeric_result,
)


class TestValueParser:
    """Test value parsing functions"""

    def test_parse_numeric_result_int(self):
        """Test parsing integer values"""
        assert parse_numeric_result(123) == 123.0
        assert parse_numeric_result(0) == 0.0
        assert parse_numeric_result(-45) == -45.0

    def test_parse_numeric_result_float(self):
        """Test parsing float values"""
        assert parse_numeric_result(123.45) == 123.45
        assert parse_numeric_result(0.0) == 0.0
        assert parse_numeric_result(-45.67) == -45.67

    def test_parse_numeric_result_string(self):
        """Test parsing numeric strings"""
        assert parse_numeric_result("123") == 123.0
        assert parse_numeric_result("123.45") == 123.45
        assert parse_numeric_result(" 123.45 ") == 123.45
        assert parse_numeric_result("0") == 0.0

    def test_parse_numeric_result_non_numeric(self):
        """Test parsing non-numeric values"""
        assert parse_numeric_result("not a number") is None
        assert parse_numeric_result("") is None
        assert parse_numeric_result(None) is None
        assert parse_numeric_result([]) is None
        assert parse_numeric_result({}) is None

    def test_parse_blood_pressure_valid(self):
        """Test parsing valid blood pressure strings"""
        systolic, diastolic = parse_blood_pressure("120/80")
        assert systolic == 120
        assert diastolic == 80

        systolic, diastolic = parse_blood_pressure("135/90")
        assert systolic == 135
        assert diastolic == 90

        systolic, diastolic = parse_blood_pressure(" 140/95 ")
        assert systolic == 140
        assert diastolic == 95

    def test_parse_blood_pressure_invalid(self):
        """Test parsing invalid blood pressure values"""
        # Invalid format
        systolic, diastolic = parse_blood_pressure("120-80")
        assert systolic is None
        assert diastolic is None

        # Not a blood pressure
        systolic, diastolic = parse_blood_pressure("120")
        assert systolic is None
        assert diastolic is None

        # Non-numeric
        systolic, diastolic = parse_blood_pressure("abc/def")
        assert systolic is None
        assert diastolic is None

        # None/empty
        systolic, diastolic = parse_blood_pressure(None)
        assert systolic is None
        assert diastolic is None

        systolic, diastolic = parse_blood_pressure("")
        assert systolic is None
        assert diastolic is None

    def test_parse_blood_pressure_non_string(self):
        """Test parsing non-string blood pressure values"""
        systolic, diastolic = parse_blood_pressure(123)
        assert systolic is None
        assert diastolic is None

        systolic, diastolic = parse_blood_pressure([])
        assert systolic is None
        assert diastolic is None
