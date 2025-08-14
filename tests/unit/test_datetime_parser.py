"""Tests for datetime parser"""

from datetime import datetime, timezone

from src.services.parsers.patient.datetime_parser import (
    format_date,
    format_datetime,
    parse_date,
    parse_datetime,
)


class TestDatetimeParser:
    """Test datetime parsing functions"""

    def test_parse_datetime_full_format(self):
        """Test parsing full datetime format"""
        # Full format: YYYYMMDDHHMMSS
        result = parse_datetime(20240115143045)
        assert result == datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)

    def test_parse_datetime_date_only(self):
        """Test parsing date only format"""
        # Date only: YYYYMMDD
        result = parse_datetime(20240115)
        assert result == datetime(2024, 1, 15, tzinfo=timezone.utc)

    def test_parse_datetime_with_hour_minute(self):
        """Test parsing datetime with hour and minute"""
        # YYYYMMDDHHMM
        result = parse_datetime(202401151430)
        assert result == datetime(2024, 1, 15, 14, 30, tzinfo=timezone.utc)

    def test_parse_datetime_string_input(self):
        """Test parsing datetime from string"""
        result = parse_datetime("20240115143045")
        assert result == datetime(2024, 1, 15, 14, 30, 45, tzinfo=timezone.utc)

    def test_parse_datetime_none(self):
        """Test parsing None returns None"""
        assert parse_datetime(None) is None

    def test_parse_datetime_invalid(self):
        """Test parsing invalid datetime returns None"""
        assert parse_datetime(999) is None
        assert parse_datetime("invalid") is None

    def test_parse_date(self):
        """Test parsing date format"""
        result = parse_date(20240115)
        assert result == datetime(2024, 1, 15).date()

    def test_parse_date_none(self):
        """Test parsing None date returns None"""
        assert parse_date(None) is None

    def test_format_datetime(self):
        """Test formatting datetime"""
        dt = datetime(2024, 1, 15, 14, 30, 45)
        result = format_datetime(dt)
        assert result == 20240115143045

    def test_format_datetime_none(self):
        """Test formatting None datetime"""
        assert format_datetime(None) is None

    def test_format_date(self):
        """Test formatting date"""
        dt = datetime(2024, 1, 15).date()
        result = format_date(dt)
        assert result == 20240115

    def test_format_date_none(self):
        """Test formatting None date"""
        assert format_date(None) is None
