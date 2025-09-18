"""
Comprehensive test patients with diverse veteran scenarios
"""

from typing import Any

# Test patients covering various veteran demographics and conditions
TEST_PATIENTS: dict[str, dict[str, Any]] = {
    # Vietnam Era Veteran with PTSD and Agent Orange exposure
    "100022": {
        "name": "ANDERSON,JAMES ROBERT",
        "ssn": "***-**-6789",
        "dob": "19450315",
        "age": 79,
        "gender": "M",
        "race": "WHITE",
        "ethnicity": "NOT HISPANIC",
        "maritalStatus": "MARRIED",
        "religion": "PROTESTANT",
        "address": "123 VETERANS DRIVE, ARLINGTON, VA 22201",
        "phone": "(703) 555-0134",
        "cellPhone": "(703) 555-0135",
        "workPhone": "",
        "email": "janderson@email.com",
        "emergencyContact": {
            "name": "ANDERSON,MARY",
            "relationship": "SPOUSE",
            "phone": "(703) 555-0135",
        },
        "insurance": {
            "primary": "MEDICARE",
            "secondary": "VA HEALTH CARE",
            "tertiary": "",
        },
        "veteranStatus": {
            "serviceConnected": True,
            "serviceConnectedPercent": 70,
            "combatVeteran": True,
            "purpleHeart": False,
            "formerPOW": False,
        },
        "military": {
            "branch": "ARMY",
            "serviceEra": "VIETNAM",
            "dischargeStatus": "HONORABLE",
            "serviceYears": "1965-1969",
        },
        "eligibility": {
            "priorityGroup": "GROUP 1",
            "enrollmentDate": "19950815",
            "meansTestStatus": "NOT REQUIRED",
            "copayStatus": "EXEMPT",
        },
        "flags": ["COMBAT VETERAN", "AGENT ORANGE EXPOSURE", "HIGH RISK FOR SUICIDE"],
    },
    # Female Gulf War Veteran with MST
    "1000000219V596118": {
        "name": "MARTINEZ,MARIA ELENA",
        "ssn": "***-**-5678",
        "dob": "19700522",
        "age": 54,
        "gender": "F",
        "race": "WHITE",
        "ethnicity": "HISPANIC",
        "maritalStatus": "DIVORCED",
        "religion": "CATHOLIC",
        "address": "456 OAK STREET APT 2B, ATLANTA, GA 30303",
        "phone": "(404) 555-0234",
        "cellPhone": "(404) 555-0235",
        "workPhone": "(404) 555-0236",
        "email": "mmartinez@email.com",
        "emergencyContact": {
            "name": "MARTINEZ,CARLOS",
            "relationship": "BROTHER",
            "phone": "(404) 555-0237",
        },
        "insurance": {
            "primary": "VA HEALTH CARE",
            "secondary": "PRIVATE - BLUE CROSS",
            "tertiary": "",
        },
        "veteranStatus": {
            "serviceConnected": True,
            "serviceConnectedPercent": 50,
            "combatVeteran": True,
            "purpleHeart": False,
            "formerPOW": False,
        },
        "military": {
            "branch": "AIR FORCE",
            "serviceEra": "GULF WAR",
            "dischargeStatus": "HONORABLE",
            "serviceYears": "1989-1995",
        },
        "eligibility": {
            "priorityGroup": "GROUP 2",
            "enrollmentDate": "19960322",
            "meansTestStatus": "CURRENT",
            "copayStatus": "REQUIRED",
        },
        "flags": ["MILITARY SEXUAL TRAUMA", "WOMEN'S HEALTH", "GULF WAR VETERAN"],
    },
    # OEF/OIF Veteran with Polytrauma
    "100024": {
        "name": "THOMPSON,MICHAEL DAVID",
        "ssn": "***-**-4567",
        "dob": "19850718",
        "age": 39,
        "gender": "M",
        "race": "BLACK",
        "ethnicity": "NOT HISPANIC",
        "maritalStatus": "MARRIED",
        "religion": "BAPTIST",
        "address": "789 PINE AVENUE, DALLAS, TX 75201",
        "phone": "(214) 555-0334",
        "cellPhone": "(214) 555-0335",
        "workPhone": "",
        "email": "mthompson@email.com",
        "emergencyContact": {
            "name": "THOMPSON,ANGELA",
            "relationship": "SPOUSE",
            "phone": "(214) 555-0336",
        },
        "insurance": {"primary": "VA HEALTH CARE", "secondary": "", "tertiary": ""},
        "veteranStatus": {
            "serviceConnected": True,
            "serviceConnectedPercent": 100,
            "combatVeteran": True,
            "purpleHeart": True,
            "formerPOW": False,
        },
        "military": {
            "branch": "MARINE CORPS",
            "serviceEra": "OEF/OIF",
            "dischargeStatus": "MEDICAL",
            "serviceYears": "2003-2010",
        },
        "eligibility": {
            "priorityGroup": "GROUP 1",
            "enrollmentDate": "20100815",
            "meansTestStatus": "NOT REQUIRED",
            "copayStatus": "EXEMPT",
        },
        "flags": [
            "POLYTRAUMA",
            "TBI",
            "AMPUTEE",
            "PURPLE HEART RECIPIENT",
            "OEF/OIF VETERAN",
        ],
    },
    # Elderly Korean War Veteran in Long-term Care
    "100025": {
        "name": "WILLIAMS,ROBERT EARL",
        "ssn": "***-**-3456",
        "dob": "19300825",
        "age": 94,
        "gender": "M",
        "race": "WHITE",
        "ethnicity": "NOT HISPANIC",
        "maritalStatus": "WIDOWED",
        "religion": "METHODIST",
        "address": "VA CLC UNIT 3B, PALO ALTO, CA 94304",
        "phone": "(650) 555-0434",
        "cellPhone": "",
        "workPhone": "",
        "email": "",
        "emergencyContact": {
            "name": "WILLIAMS,SUSAN",
            "relationship": "DAUGHTER",
            "phone": "(650) 555-0435",
        },
        "insurance": {
            "primary": "MEDICARE",
            "secondary": "VA HEALTH CARE",
            "tertiary": "MEDICAID",
        },
        "veteranStatus": {
            "serviceConnected": True,
            "serviceConnectedPercent": 40,
            "combatVeteran": True,
            "purpleHeart": False,
            "formerPOW": True,
        },
        "military": {
            "branch": "ARMY",
            "serviceEra": "KOREAN WAR",
            "dischargeStatus": "HONORABLE",
            "serviceYears": "1950-1954",
        },
        "eligibility": {
            "priorityGroup": "GROUP 3",
            "enrollmentDate": "19850315",
            "meansTestStatus": "NOT REQUIRED",
            "copayStatus": "EXEMPT",
        },
        "flags": [
            "LONG TERM CARE",
            "FORMER POW",
            "FALL RISK",
            "DEMENTIA",
            "KOREAN WAR VETERAN",
        ],
    },
    # Homeless Veteran with Substance Abuse
    "100026": {
        "name": "JOHNSON,DAVID WAYNE",
        "ssn": "***-**-2345",
        "dob": "19750412",
        "age": 49,
        "gender": "M",
        "race": "WHITE",
        "ethnicity": "NOT HISPANIC",
        "maritalStatus": "DIVORCED",
        "religion": "NONE",
        "address": "HOMELESS - TAMPA AREA",
        "phone": "(813) 555-0534",
        "cellPhone": "",
        "workPhone": "",
        "email": "",
        "emergencyContact": {
            "name": "VA SOCIAL WORK",
            "relationship": "CASE MANAGER",
            "phone": "(813) 972-2000",
        },
        "insurance": {"primary": "VA HEALTH CARE", "secondary": "", "tertiary": ""},
        "veteranStatus": {
            "serviceConnected": False,
            "serviceConnectedPercent": 0,
            "combatVeteran": False,
            "purpleHeart": False,
            "formerPOW": False,
        },
        "military": {
            "branch": "NAVY",
            "serviceEra": "PEACETIME",
            "dischargeStatus": "GENERAL",
            "serviceYears": "1993-1997",
        },
        "eligibility": {
            "priorityGroup": "GROUP 5",
            "enrollmentDate": "20150612",
            "meansTestStatus": "CURRENT",
            "copayStatus": "EXEMPT",
        },
        "flags": ["HOMELESS", "SUBSTANCE ABUSE", "HIGH RISK", "CASE MANAGEMENT"],
    },
    # Recent Female Veteran with Mental Health Needs
    "100027": {
        "name": "DAVIS,JENNIFER LYNN",
        "ssn": "***-**-1234",
        "dob": "19950228",
        "age": 29,
        "gender": "F",
        "race": "BLACK",
        "ethnicity": "NOT HISPANIC",
        "maritalStatus": "SINGLE",
        "religion": "CHRISTIAN",
        "address": "321 MAPLE DRIVE APT 5C, WASHINGTON, DC 20001",
        "phone": "(202) 555-0634",
        "cellPhone": "(202) 555-0635",
        "workPhone": "(202) 555-0636",
        "email": "jdavis@email.com",
        "emergencyContact": {
            "name": "DAVIS,PATRICIA",
            "relationship": "MOTHER",
            "phone": "(202) 555-0637",
        },
        "insurance": {
            "primary": "PRIVATE - EMPLOYER",
            "secondary": "VA HEALTH CARE",
            "tertiary": "",
        },
        "veteranStatus": {
            "serviceConnected": True,
            "serviceConnectedPercent": 30,
            "combatVeteran": False,
            "purpleHeart": False,
            "formerPOW": False,
        },
        "military": {
            "branch": "ARMY",
            "serviceEra": "POST-9/11",
            "dischargeStatus": "HONORABLE",
            "serviceYears": "2014-2022",
        },
        "eligibility": {
            "priorityGroup": "GROUP 2",
            "enrollmentDate": "20220815",
            "meansTestStatus": "NOT REQUIRED",
            "copayStatus": "REQUIRED",
        },
        "flags": [
            "POST-9/11 VETERAN",
            "WOMEN'S HEALTH",
            "MENTAL HEALTH",
            "TRANSITION ASSISTANCE",
        ],
    },
    # Rural Veteran with Telehealth Needs
    "100028": {
        "name": "WILSON,GEORGE HENRY",
        "ssn": "***-**-0123",
        "dob": "19550610",
        "age": 69,
        "gender": "M",
        "race": "WHITE",
        "ethnicity": "NOT HISPANIC",
        "maritalStatus": "MARRIED",
        "religion": "LUTHERAN",
        "address": "RR 2 BOX 145, RURAL ROUTE, GA 31605",
        "phone": "(229) 555-0734",
        "cellPhone": "(229) 555-0735",
        "workPhone": "",
        "email": "gwilson@email.com",
        "emergencyContact": {
            "name": "WILSON,BETTY",
            "relationship": "SPOUSE",
            "phone": "(229) 555-0735",
        },
        "insurance": {
            "primary": "MEDICARE",
            "secondary": "VA HEALTH CARE",
            "tertiary": "PRIVATE SUPPLEMENT",
        },
        "veteranStatus": {
            "serviceConnected": True,
            "serviceConnectedPercent": 60,
            "combatVeteran": True,
            "purpleHeart": False,
            "formerPOW": False,
        },
        "military": {
            "branch": "AIR FORCE",
            "serviceEra": "VIETNAM",
            "dischargeStatus": "RETIREMENT",
            "serviceYears": "1973-1993",
        },
        "eligibility": {
            "priorityGroup": "GROUP 1",
            "enrollmentDate": "19930915",
            "meansTestStatus": "NOT REQUIRED",
            "copayStatus": "EXEMPT",
        },
        "flags": [
            "RURAL VETERAN",
            "TELEHEALTH ENROLLED",
            "TRAVEL PAY ELIGIBLE",
            "VIETNAM VETERAN",
        ],
    },
    # Veteran with Complex Medical Needs
    "100029": {
        "name": "GARCIA,ANTONIO JOSE",
        "ssn": "***-**-9012",
        "dob": "19600118",
        "age": 64,
        "gender": "M",
        "race": "WHITE",
        "ethnicity": "HISPANIC",
        "maritalStatus": "MARRIED",
        "religion": "CATHOLIC",
        "address": "567 MISSION STREET, PALO ALTO, CA 94301",
        "phone": "(650) 555-0834",
        "cellPhone": "(650) 555-0835",
        "workPhone": "",
        "email": "agarcia@email.com",
        "emergencyContact": {
            "name": "GARCIA,ROSA",
            "relationship": "SPOUSE",
            "phone": "(650) 555-0835",
        },
        "insurance": {
            "primary": "VA HEALTH CARE",
            "secondary": "MEDICARE",
            "tertiary": "",
        },
        "veteranStatus": {
            "serviceConnected": True,
            "serviceConnectedPercent": 80,
            "combatVeteran": False,
            "purpleHeart": False,
            "formerPOW": False,
        },
        "military": {
            "branch": "NAVY",
            "serviceEra": "PEACETIME",
            "dischargeStatus": "HONORABLE",
            "serviceYears": "1978-1982",
        },
        "eligibility": {
            "priorityGroup": "GROUP 1",
            "enrollmentDate": "19900215",
            "meansTestStatus": "NOT REQUIRED",
            "copayStatus": "EXEMPT",
        },
        "flags": [
            "DIABETIC",
            "DIALYSIS PATIENT",
            "TRANSPLANT CANDIDATE",
            "HIGH UTILIZER",
        ],
    },
}


def get_patient_by_dfn_or_icn(dfn_or_icn: str) -> dict[str, Any]:
    """Get patient data by DFN"""
    return TEST_PATIENTS.get(
        dfn_or_icn,
        {
            "name": "TEST,PATIENT",
            "ssn": "***-**-0000",
            "dob": "20000101",
            "age": 24,
            "gender": "U",
            "address": "UNKNOWN",
            "phone": "(000) 000-0000",
            "emergencyContact": {
                "name": "NONE",
                "relationship": "NONE",
                "phone": "(000) 000-0000",
            },
        },
    )


def search_patients_by_name(prefix: str) -> list[dict[str, Any]]:
    """Search patients by name prefix"""
    prefix_upper = prefix.upper()
    results = []

    for dfn, patient in TEST_PATIENTS.items():
        if patient["name"].upper().startswith(prefix_upper):
            results.append(
                {
                    "dfn": dfn,
                    "name": patient["name"],
                    "ssn": patient["ssn"],
                    "dob": patient["dob"],
                    "gender": patient["gender"],
                }
            )

    return results
