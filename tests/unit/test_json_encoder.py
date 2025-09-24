"""Tests for the custom JSON encoder"""

import json
from datetime import date, datetime

from src.services.cache.json_encoder import DateTimeJSONEncoder


def test_datetime_encoding():
    """Test that datetime objects are properly encoded"""
    dt = datetime(2023, 1, 15, 10, 30, 45)
    result = json.dumps({"timestamp": dt}, cls=DateTimeJSONEncoder)
    assert '"2023-01-15T10:30:45"' in result


def test_date_encoding():
    """Test that date objects are properly encoded"""
    d = date(2023, 1, 15)
    result = json.dumps({"birth_date": d}, cls=DateTimeJSONEncoder)
    assert '"2023-01-15"' in result


def test_mixed_data_encoding():
    """Test encoding of mixed data types"""
    data = {
        "name": "Test Patient",
        "birth_date": date(1990, 5, 20),
        "last_visit": datetime(2023, 12, 1, 14, 30),
        "age": 33,
        "active": True,
        "notes": None,
        "scores": [1, 2, 3],
    }

    result = json.dumps(data, cls=DateTimeJSONEncoder)
    decoded = json.loads(result)

    assert decoded["name"] == "Test Patient"
    assert decoded["birth_date"] == "1990-05-20"
    assert decoded["last_visit"] == "2023-12-01T14:30:00"
    assert decoded["age"] == 33
    assert decoded["active"] is True
    assert decoded["notes"] is None
    assert decoded["scores"] == [1, 2, 3]


def test_nested_datetime_encoding():
    """Test encoding of nested structures with datetime objects"""
    data = {
        "patient": {
            "id": "123",
            "demographics": {
                "birth_date": date(1985, 3, 15),
                "created": datetime(2020, 1, 1, 0, 0, 0),
            },
        }
    }

    result = json.dumps(data, cls=DateTimeJSONEncoder)
    decoded = json.loads(result)

    assert decoded["patient"]["demographics"]["birth_date"] == "1985-03-15"
    assert decoded["patient"]["demographics"]["created"] == "2020-01-01T00:00:00"
