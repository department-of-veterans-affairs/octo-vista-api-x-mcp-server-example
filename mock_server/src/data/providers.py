"""
VA Providers test data - Realistic VA staff profiles
"""

# Test providers with realistic VA roles
VA_PROVIDERS: dict[str, dict[str, str]] = {
    "10000000219": {
        "name": "SMITH,JENNIFER A",
        "title": "MD",
        "service": "PRIMARY CARE",
        "role": "PHYSICIAN",
        "specialty": "INTERNAL MEDICINE",
        "dea": "BS1234567",
        "npi": "1234567890",
        "phone": "(202) 745-8234",
        "email": "jennifer.smith@va.gov",
        "cosigner": "",
        "defaultLocation": "PRIMARY CARE CLINIC",
    },
    "10000000220": {
        "name": "JOHNSON,MICHAEL R",
        "title": "RN",
        "service": "EMERGENCY MEDICINE",
        "role": "NURSE PRACTITIONER",
        "specialty": "EMERGENCY CARE",
        "dea": "",
        "npi": "2345678901",
        "phone": "(404) 321-6234",
        "email": "michael.johnson@va.gov",
        "cosigner": "10000000219",
        "defaultLocation": "EMERGENCY DEPARTMENT",
    },
    "10000000221": {
        "name": "WILLIAMS,PATRICIA L",
        "title": "MD",
        "service": "MENTAL HEALTH",
        "role": "PSYCHIATRIST",
        "specialty": "PSYCHIATRY",
        "dea": "BW2345678",
        "npi": "3456789012",
        "phone": "(650) 493-5234",
        "email": "patricia.williams@va.gov",
        "cosigner": "",
        "defaultLocation": "MENTAL HEALTH CLINIC",
    },
    "10000000222": {
        "name": "MARTINEZ,CARLOS E",
        "title": "MD",
        "service": "SURGICAL SERVICE",
        "role": "SURGEON",
        "specialty": "ORTHOPEDIC SURGERY",
        "dea": "BM3456789",
        "npi": "4567890123",
        "phone": "(214) 742-8234",
        "email": "carlos.martinez@va.gov",
        "cosigner": "",
        "defaultLocation": "ORTHOPEDIC CLINIC",
    },
    "10000000223": {
        "name": "DAVIS,ROBERT J",
        "title": "PHARMD",
        "service": "PHARMACY SERVICE",
        "role": "CLINICAL PHARMACIST",
        "specialty": "PHARMACY",
        "dea": "",
        "npi": "5678901234",
        "phone": "(813) 972-2234",
        "email": "robert.davis@va.gov",
        "cosigner": "",
        "defaultLocation": "OUTPATIENT PHARMACY",
    },
    "10000000224": {
        "name": "THOMPSON,MICHELLE K",
        "title": "PHD",
        "service": "MENTAL HEALTH",
        "role": "PSYCHOLOGIST",
        "specialty": "CLINICAL PSYCHOLOGY",
        "dea": "",
        "npi": "6789012345",
        "phone": "(202) 745-8345",
        "email": "michelle.thompson@va.gov",
        "cosigner": "10000000221",
        "defaultLocation": "PSYCHOLOGY CLINIC",
    },
    "10000000225": {
        "name": "ANDERSON,DAVID W",
        "title": "MD",
        "service": "SPECIALTY CARE",
        "role": "PHYSICIAN",
        "specialty": "CARDIOLOGY",
        "dea": "BA4567890",
        "npi": "7890123456",
        "phone": "(404) 321-6345",
        "email": "david.anderson@va.gov",
        "cosigner": "",
        "defaultLocation": "CARDIOLOGY CLINIC",
    },
    "10000000226": {
        "name": "GARCIA,MARIA S",
        "title": "RN",
        "service": "PRIMARY CARE",
        "role": "CARE COORDINATOR",
        "specialty": "CASE MANAGEMENT",
        "dea": "",
        "npi": "8901234567",
        "phone": "(650) 493-5345",
        "email": "maria.garcia@va.gov",
        "cosigner": "10000000219",
        "defaultLocation": "PRIMARY CARE CLINIC",
    },
    "10000000227": {
        "name": "WILSON,JAMES T",
        "title": "LCSW",
        "service": "MENTAL HEALTH",
        "role": "SOCIAL WORKER",
        "specialty": "CLINICAL SOCIAL WORK",
        "dea": "",
        "npi": "9012345678",
        "phone": "(214) 742-8456",
        "email": "james.wilson@va.gov",
        "cosigner": "10000000221",
        "defaultLocation": "SOCIAL WORK SERVICE",
    },
    "10000000228": {
        "name": "BROWN,SARAH E",
        "title": "MD",
        "service": "SPECIALTY CARE",
        "role": "PHYSICIAN",
        "specialty": "ENDOCRINOLOGY",
        "dea": "BB5678901",
        "npi": "0123456789",
        "phone": "(813) 972-2456",
        "email": "sarah.brown@va.gov",
        "cosigner": "",
        "defaultLocation": "DIABETIC CLINIC",
    },
}

# Provider types in VA
PROVIDER_TYPES: list[str] = [
    "PHYSICIAN",
    "NURSE PRACTITIONER",
    "PHYSICIAN ASSISTANT",
    "CLINICAL NURSE SPECIALIST",
    "PSYCHIATRIST",
    "PSYCHOLOGIST",
    "SOCIAL WORKER",
    "CLINICAL PHARMACIST",
    "PHYSICAL THERAPIST",
    "OCCUPATIONAL THERAPIST",
    "DIETITIAN",
    "RESPIRATORY THERAPIST",
    "AUDIOLOGIST",
    "OPTOMETRIST",
    "PODIATRIST",
    "DENTIST",
    "SPEECH THERAPIST",
    "CARE COORDINATOR",
    "PEER SUPPORT SPECIALIST",
]

# Common VA provider titles
PROVIDER_TITLES: list[str] = [
    "MD",
    "DO",
    "NP",
    "PA",
    "RN",
    "PHARMD",
    "PHD",
    "PSYD",
    "LCSW",
    "LICSW",
    "DPT",
    "OTD",
    "RD",
    "AUD",
    "OD",
    "DPM",
    "DDS",
    "DMD",
    "CCC-SLP",
]


def get_provider_by_duz(duz: str) -> dict[str, str]:
    """Get provider information by DUZ"""
    return VA_PROVIDERS.get(
        duz,
        {
            "name": "PROVIDER,TEST",
            "title": "MD",
            "service": "UNKNOWN SERVICE",
            "role": "PROVIDER",
            "specialty": "UNKNOWN",
            "dea": "",
            "npi": "9999999999",
            "phone": "(000) 000-0000",
            "email": "test.provider@va.gov",
            "cosigner": "",
            "defaultLocation": "UNKNOWN LOCATION",
        },
    )


def get_providers_by_service(service: str) -> list[dict[str, str]]:
    """Get all providers in a service"""
    return [
        provider for provider in VA_PROVIDERS.values() if provider["service"] == service
    ]


def get_providers_by_role(role: str) -> list[dict[str, str]]:
    """Get all providers with a specific role"""
    return [provider for provider in VA_PROVIDERS.values() if provider["role"] == role]
