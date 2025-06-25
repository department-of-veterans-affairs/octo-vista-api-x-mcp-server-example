"""
VA Facilities test data - Real VA Medical Centers
"""

from typing import Dict, List

# Real VA Medical Centers across the US
VA_FACILITIES: Dict[str, Dict[str, str]] = {
    "500": {
        "name": "WASHINGTON DC VA MEDICAL CENTER",
        "address": "50 IRVING STREET NW, WASHINGTON, DC 20422",
        "phone": "(202) 745-8000",
        "region": "VISN 5",
        "complexity": "1a",
        "type": "VAMC"
    },
    "508": {
        "name": "ATLANTA VA MEDICAL CENTER",
        "address": "1670 CLAIRMONT ROAD, DECATUR, GA 30033",
        "phone": "(404) 321-6111",
        "region": "VISN 7",
        "complexity": "1a",
        "type": "VAMC"
    },
    "549": {
        "name": "NORTH TEXAS HCS (DALLAS)",
        "address": "4500 S LANCASTER ROAD, DALLAS, TX 75216",
        "phone": "(214) 742-8387",
        "region": "VISN 17",
        "complexity": "1a",
        "type": "VAMC"
    },
    "640": {
        "name": "PALO ALTO VA MEDICAL CENTER",
        "address": "3801 MIRANDA AVENUE, PALO ALTO, CA 94304",
        "phone": "(650) 493-5000",
        "region": "VISN 21",
        "complexity": "1a",
        "type": "VAMC"
    },
    "673": {
        "name": "TAMPA VA MEDICAL CENTER",
        "address": "13000 BRUCE B DOWNS BLVD, TAMPA, FL 33612",
        "phone": "(813) 972-2000",
        "region": "VISN 8",
        "complexity": "1a",
        "type": "VAMC"
    },
    "999": {
        "name": "TEST MEDICAL CENTER",
        "address": "123 TEST STREET, TESTVILLE, VA 00000",
        "phone": "(000) 000-0000",
        "region": "TEST VISN",
        "complexity": "TEST",
        "type": "TEST"
    }
}

# Clinic types available at VA facilities
VA_CLINIC_TYPES: List[Dict[str, str]] = [
    {"code": "323", "name": "PRIMARY CARE", "stopCode": "323"},
    {"code": "303", "name": "CARDIOLOGY", "stopCode": "303"},
    {"code": "407", "name": "DIABETIC", "stopCode": "407"},
    {"code": "502", "name": "MENTAL HEALTH", "stopCode": "502"},
    {"code": "203", "name": "ORTHOPEDIC", "stopCode": "203"},
    {"code": "209", "name": "NEUROLOGY", "stopCode": "209"},
    {"code": "322", "name": "WOMEN'S HEALTH", "stopCode": "322"},
    {"code": "130", "name": "EMERGENCY", "stopCode": "130"},
    {"code": "108", "name": "LABORATORY", "stopCode": "108"},
    {"code": "105", "name": "RADIOLOGY", "stopCode": "105"},
    {"code": "316", "name": "PHARMACY", "stopCode": "316"},
    {"code": "409", "name": "PAIN CLINIC", "stopCode": "409"},
    {"code": "324", "name": "GERIATRICS", "stopCode": "324"},
    {"code": "330", "name": "DERMATOLOGY", "stopCode": "330"},
    {"code": "403", "name": "AUDIOLOGY", "stopCode": "403"},
    {"code": "408", "name": "OPTOMETRY", "stopCode": "408"},
    {"code": "419", "name": "REHABILITATION", "stopCode": "419"},
    {"code": "511", "name": "SUBSTANCE ABUSE", "stopCode": "511"},
    {"code": "590", "name": "TELEHEALTH", "stopCode": "590"},
    {"code": "680", "name": "HOME CARE", "stopCode": "680"}
]

# Service lines at VA
VA_SERVICE_LINES: List[str] = [
    "PRIMARY CARE",
    "MENTAL HEALTH",
    "SPECIALTY CARE",
    "SURGICAL SERVICE",
    "DIAGNOSTIC SERVICE",
    "EMERGENCY MEDICINE",
    "REHABILITATION",
    "EXTENDED CARE",
    "DENTAL SERVICE",
    "PHARMACY SERVICE"
]

def get_facility_by_station(station: str) -> Dict[str, str]:
    """Get facility information by station number"""
    # Handle 6-character station codes by taking first 3 digits
    station_3digit = station[:3] if len(station) >= 3 else station
    return VA_FACILITIES.get(station_3digit, VA_FACILITIES["999"])

def get_clinics_for_station(station: str) -> List[Dict[str, str]]:
    """Get available clinics for a station"""
    # In reality, different facilities have different clinics
    # For mock, return common clinics
    return VA_CLINIC_TYPES[:10]  # Return first 10 common clinics