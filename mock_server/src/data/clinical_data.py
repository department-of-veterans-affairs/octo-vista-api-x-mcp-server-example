"""
Comprehensive clinical data for test patients
"""


# Problems/Diagnoses by patient
PATIENT_PROBLEMS: dict[str, list[dict[str, str]]] = {
    # Vietnam Veteran with PTSD
    "100022": [
        {
            "icd10": "F43.12",
            "description": "POST TRAUMATIC STRESS DISORDER, CHRONIC",
            "status": "ACTIVE",
            "onsetDate": "19700615",
            "provider": "WILLIAMS,PATRICIA L",
        },
        {
            "icd10": "E11.40",
            "description": "TYPE 2 DIABETES MELLITUS WITH DIABETIC NEUROPATHY",
            "status": "ACTIVE",
            "onsetDate": "20100315",
            "provider": "SMITH,JENNIFER A",
        },
        {
            "icd10": "I10",
            "description": "ESSENTIAL HYPERTENSION",
            "status": "ACTIVE",
            "onsetDate": "20050822",
            "provider": "SMITH,JENNIFER A",
        },
        {
            "icd10": "H93.11",
            "description": "TINNITUS, RIGHT EAR",
            "status": "ACTIVE",
            "onsetDate": "19690415",
            "provider": "SMITH,JENNIFER A",
        },
        {
            "icd10": "H90.3",
            "description": "BILATERAL HEARING LOSS",
            "status": "ACTIVE",
            "onsetDate": "19850620",
            "provider": "SMITH,JENNIFER A",
        },
        {
            "icd10": "M54.5",
            "description": "CHRONIC LOW BACK PAIN",
            "status": "ACTIVE",
            "onsetDate": "19950310",
            "provider": "MARTINEZ,CARLOS E",
        },
    ],
    # Female Gulf War Veteran
    "100023": [
        {
            "icd10": "F43.10",
            "description": "POST TRAUMATIC STRESS DISORDER",
            "status": "ACTIVE",
            "onsetDate": "19950822",
            "provider": "WILLIAMS,PATRICIA L",
        },
        {
            "icd10": "F33.1",
            "description": "MAJOR DEPRESSIVE DISORDER, RECURRENT, MODERATE",
            "status": "ACTIVE",
            "onsetDate": "19960415",
            "provider": "WILLIAMS,PATRICIA L",
        },
        {
            "icd10": "G44.201",
            "description": "TENSION-TYPE HEADACHE, CHRONIC",
            "status": "ACTIVE",
            "onsetDate": "19950620",
            "provider": "SMITH,JENNIFER A",
        },
        {
            "icd10": "M79.7",
            "description": "FIBROMYALGIA",
            "status": "ACTIVE",
            "onsetDate": "19970310",
            "provider": "SMITH,JENNIFER A",
        },
    ],
    # OEF/OIF Polytrauma
    "100024": [
        {
            "icd10": "S06.2X9S",
            "description": "TRAUMATIC BRAIN INJURY, SEQUELA",
            "status": "ACTIVE",
            "onsetDate": "20080615",
            "provider": "ANDERSON,DAVID W",
        },
        {
            "icd10": "Z89.511",
            "description": "ACQUIRED ABSENCE OF RIGHT LEG BELOW KNEE",
            "status": "ACTIVE",
            "onsetDate": "20080615",
            "provider": "MARTINEZ,CARLOS E",
        },
        {
            "icd10": "F43.12",
            "description": "POST TRAUMATIC STRESS DISORDER, CHRONIC",
            "status": "ACTIVE",
            "onsetDate": "20080822",
            "provider": "WILLIAMS,PATRICIA L",
        },
        {
            "icd10": "G89.21",
            "description": "CHRONIC PAIN DUE TO TRAUMA",
            "status": "ACTIVE",
            "onsetDate": "20080615",
            "provider": "SMITH,JENNIFER A",
        },
    ],
}

# Medications by patient
PATIENT_MEDICATIONS: dict[str, list[dict[str, any]]] = {
    "100022": [
        {
            "name": "METFORMIN 1000MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH TWICE DAILY WITH MEALS",
            "quantity": "180",
            "daysSupply": "90",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "LISINOPRIL 20MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "90",
            "daysSupply": "90",
            "refills": "3",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "SERTRALINE 100MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "90",
            "daysSupply": "90",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "WILLIAMS,PATRICIA L",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "GABAPENTIN 300MG CAP",
            "sig": "TAKE 1 CAPSULE BY MOUTH THREE TIMES DAILY",
            "quantity": "270",
            "daysSupply": "90",
            "refills": "3",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "ASPIRIN 81MG EC TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "90",
            "daysSupply": "90",
            "refills": "11",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
    ],
    "100023": [
        {
            "name": "SERTRALINE 50MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "90",
            "daysSupply": "90",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "WILLIAMS,PATRICIA L",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "PRAZOSIN 2MG CAP",
            "sig": "TAKE 1 CAPSULE BY MOUTH AT BEDTIME FOR NIGHTMARES",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "11",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "WILLIAMS,PATRICIA L",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "SUMATRIPTAN 100MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH AT ONSET OF MIGRAINE, MAY REPEAT X1",
            "quantity": "9",
            "daysSupply": "30",
            "refills": "3",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
    ],
    "100024": [
        {
            "name": "MORPHINE SULFATE ER 30MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH EVERY 12 HOURS",
            "quantity": "60",
            "daysSupply": "30",
            "refills": "0",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
            "controlled": True,
        },
        {
            "name": "OXYCODONE 5MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH EVERY 4-6 HOURS AS NEEDED FOR BREAKTHROUGH PAIN",
            "quantity": "120",
            "daysSupply": "30",
            "refills": "0",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
            "controlled": True,
        },
        {
            "name": "ESCITALOPRAM 20MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "90",
            "daysSupply": "90",
            "refills": "3",
            "status": "ACTIVE",
            "orderDate": "20240101",
            "prescriber": "WILLIAMS,PATRICIA L",
            "pharmacy": "VA PHARMACY",
        },
    ],
    "100025": [
        {
            "name": "DONEPEZIL 10MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH AT BEDTIME",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240301",
            "prescriber": "JONES,MARK R",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "MEMANTINE 10MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH TWICE A DAY",
            "quantity": "60",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240301",
            "prescriber": "JONES,MARK R",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "FUROSEMIDE 40MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240301",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "LISINOPRIL 20MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240301",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "METOPROLOL TARTRATE 50MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH TWICE A DAY",
            "quantity": "60",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240301",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
    ],
    "100026": [
        {
            "name": "NALTREXONE 50MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "3",
            "status": "ACTIVE",
            "orderDate": "20240515",
            "prescriber": "DAVIS,ROBERT M",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "THIAMINE 100MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "11",
            "status": "ACTIVE",
            "orderDate": "20240515",
            "prescriber": "DAVIS,ROBERT M",
            "pharmacy": "VA PHARMACY",
        },
    ],
    "100027": [
        {
            "name": "PRENATAL VITAMINS",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "11",
            "status": "ACTIVE",
            "orderDate": "20240901",
            "prescriber": "TAYLOR,SUSAN K",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "SERTRALINE 50MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240901",
            "prescriber": "WILLIAMS,PATRICIA L",
            "pharmacy": "VA PHARMACY",
        },
    ],
    "100028": [
        {
            "name": "METFORMIN 1000MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH TWICE DAILY",
            "quantity": "60",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240201",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "LOSARTAN 50MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH DAILY",
            "quantity": "30",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240201",
            "prescriber": "SMITH,JENNIFER A",
            "pharmacy": "VA PHARMACY",
        },
    ],
    "100029": [
        {
            "name": "SEVELAMER 800MG TAB",
            "sig": "TAKE 1 TABLET BY MOUTH THREE TIMES DAILY WITH MEALS",
            "quantity": "90",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240601",
            "prescriber": "CHEN,LISA M",
            "pharmacy": "VA PHARMACY",
        },
        {
            "name": "EPOETIN ALFA 10000 UNITS/ML",
            "sig": "INJECT 10000 UNITS SUBCUTANEOUSLY THREE TIMES WEEKLY DURING DIALYSIS",
            "quantity": "12",
            "daysSupply": "30",
            "refills": "5",
            "status": "ACTIVE",
            "orderDate": "20240601",
            "prescriber": "CHEN,LISA M",
            "pharmacy": "VA PHARMACY",
        },
    ],
}

# Vital Signs by patient
PATIENT_VITALS: dict[str, list[dict[str, any]]] = {
    "100022": [
        {
            "date": "20240115T0800",
            "bp": "142/88",
            "pulse": "78",
            "temp": "98.4",
            "weight": "195",
            "height": "70",
            "bmi": "27.9",
            "resp": "16",
            "o2sat": "97",
            "pain": "4",
        },
        {
            "date": "20231015T0900",
            "bp": "138/86",
            "pulse": "76",
            "temp": "98.6",
            "weight": "193",
            "height": "70",
            "bmi": "27.7",
            "resp": "18",
            "o2sat": "98",
            "pain": "3",
        },
    ],
    "100023": [
        {
            "date": "20240110T1400",
            "bp": "118/76",
            "pulse": "68",
            "temp": "98.2",
            "weight": "142",
            "height": "66",
            "bmi": "22.9",
            "resp": "14",
            "o2sat": "99",
            "pain": "2",
        }
    ],
    "100024": [
        {
            "date": "20240118T1000",
            "bp": "124/78",
            "pulse": "82",
            "temp": "98.8",
            "weight": "168",
            "height": "69",
            "bmi": "24.8",
            "resp": "20",
            "o2sat": "96",
            "pain": "7",
        }
    ],
}

# Lab Results by patient
PATIENT_LABS: dict[str, list[dict[str, any]]] = {
    "100022": [
        {
            "test": "HEMOGLOBIN A1C",
            "value": "7.2",
            "units": "%",
            "refRange": "4.0-6.0",
            "flag": "H",
            "date": "20240110",
            "status": "FINAL",
        },
        {
            "test": "GLUCOSE",
            "value": "145",
            "units": "mg/dL",
            "refRange": "70-110",
            "flag": "H",
            "date": "20240110",
            "status": "FINAL",
        },
        {
            "test": "CREATININE",
            "value": "1.1",
            "units": "mg/dL",
            "refRange": "0.6-1.2",
            "flag": "",
            "date": "20240110",
            "status": "FINAL",
        },
        {
            "test": "POTASSIUM",
            "value": "4.2",
            "units": "mmol/L",
            "refRange": "3.5-5.1",
            "flag": "",
            "date": "20240110",
            "status": "FINAL",
        },
        {
            "test": "TSH",
            "value": "2.5",
            "units": "mIU/L",
            "refRange": "0.4-4.0",
            "flag": "",
            "date": "20240110",
            "status": "FINAL",
        },
    ],
    "100023": [
        {
            "test": "CBC WITH DIFF",
            "value": "SEE BELOW",
            "units": "",
            "refRange": "",
            "flag": "",
            "date": "20240105",
            "status": "FINAL",
            "components": [
                {"name": "WBC", "value": "6.5", "units": "K/uL", "refRange": "4.5-11.0"},
                {"name": "RBC", "value": "4.2", "units": "M/uL", "refRange": "4.0-5.2"},
                {"name": "HGB", "value": "13.5", "units": "g/dL", "refRange": "12.0-16.0"},
                {"name": "HCT", "value": "40.5", "units": "%", "refRange": "36.0-46.0"},
                {"name": "PLT", "value": "225", "units": "K/uL", "refRange": "150-400"},
            ],
        }
    ],
}

# Allergies by patient
PATIENT_ALLERGIES: dict[str, list[dict[str, str]]] = {
    "100022": [
        {
            "allergen": "PENICILLIN",
            "reaction": "HIVES",
            "severity": "MODERATE",
            "type": "DRUG",
            "verifiedDate": "19850315",
        },
        {"allergen": "SULFA DRUGS", "reaction": "RASH", "severity": "MILD", "type": "DRUG", "verifiedDate": "19900822"},
    ],
    "100023": [
        {
            "allergen": "CODEINE",
            "reaction": "NAUSEA AND VOMITING",
            "severity": "MODERATE",
            "type": "DRUG",
            "verifiedDate": "19950415",
        },
        {
            "allergen": "LATEX",
            "reaction": "CONTACT DERMATITIS",
            "severity": "MILD",
            "type": "OTHER",
            "verifiedDate": "20100620",
        },
    ],
    "100024": [
        {"allergen": "NO KNOWN ALLERGIES", "reaction": "", "severity": "", "type": "NKA", "verifiedDate": "20080615"}
    ],
    "100025": [
        {
            "allergen": "PENICILLIN",
            "reaction": "ANAPHYLAXIS",
            "severity": "SEVERE",
            "type": "DRUG",
            "dateEntered": "19900315",
            "verified": "VERIFIED",
        }
    ],
    "100026": [
        {
            "allergen": "SULFA DRUGS",
            "reaction": "RASH",
            "severity": "MODERATE",
            "type": "DRUG",
            "dateEntered": "19980612",
            "verified": "VERIFIED",
        }
    ],
    "100027": [
        {
            "allergen": "ASPIRIN",
            "reaction": "GI UPSET",
            "severity": "MILD",
            "type": "DRUG",
            "dateEntered": "20220915",
            "verified": "VERIFIED",
        }
    ],
    "100028": [
        {
            "allergen": "LISINOPRIL",
            "reaction": "COUGH",
            "severity": "MILD",
            "type": "DRUG",
            "dateEntered": "20200601",
            "verified": "VERIFIED",
        },
        {
            "allergen": "CODEINE",
            "reaction": "NAUSEA",
            "severity": "MODERATE",
            "type": "DRUG",
            "dateEntered": "20200601",
            "verified": "OBSERVED",
        },
    ],
    "100029": [
        {
            "allergen": "CONTRAST DYE",
            "reaction": "ANAPHYLAXIS",
            "severity": "SEVERE",
            "type": "DRUG",
            "dateEntered": "20150415",
            "verified": "VERIFIED",
        }
    ],
}


def get_clinical_data_for_patient(dfn: str, domain: str) -> list[dict[str, any]]:
    """Get clinical data for a patient by domain"""
    domain_map = {
        "problem": PATIENT_PROBLEMS,
        "med": PATIENT_MEDICATIONS,
        "vital": PATIENT_VITALS,
        "lab": PATIENT_LABS,
        "allergy": PATIENT_ALLERGIES,
    }

    data_dict = domain_map.get(domain, {})
    return data_dict.get(dfn, [])
