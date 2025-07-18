"""
Appointment data for test patients
"""

from datetime import datetime, timedelta


# Generate realistic appointment data
def generate_appointment_date(days_offset: int) -> str:
    """Generate appointment date relative to today"""
    date = datetime.now() + timedelta(days=days_offset)
    return date.strftime("%Y-%m-%dT%H:%M:%S")


# Appointments by patient
PATIENT_APPOINTMENTS: dict[str, list[dict[str, any]]] = {
    # Vietnam Veteran - Regular chronic care
    "100022": [
        {
            "appointmentIEN": "1234567",
            "date": generate_appointment_date(30),
            "time": "09:00",
            "clinicIEN": "195",
            "clinicName": "PRIMARY CARE CLINIC",
            "clinicStopCode": "323",
            "provider": {"duz": "10000000221", "name": "SMITH,JENNIFER A"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "30",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "DIABETES FOLLOW UP",
        },
        {
            "appointmentIEN": "1234568",
            "date": generate_appointment_date(45),
            "time": "14:30",
            "clinicIEN": "196",
            "clinicName": "MENTAL HEALTH CLINIC",
            "clinicStopCode": "502",
            "provider": {"duz": "10000000220", "name": "WILLIAMS,PATRICIA L"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "60",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "PTSD THERAPY",
        },
        {
            "appointmentIEN": "1234569",
            "date": generate_appointment_date(-30),
            "time": "10:00",
            "clinicIEN": "197",
            "clinicName": "DIABETIC CLINIC",
            "clinicStopCode": "407",
            "provider": {"duz": "10000000228", "name": "BROWN,SARAH E"},
            "status": "COMPLETED",
            "type": "REGULAR",
            "length": "30",
            "checkInTime": "09:45",
            "checkOutTime": "10:35",
            "purpose": "DIABETIC EDUCATION",
        },
        {
            "appointmentIEN": "1234570",
            "date": generate_appointment_date(90),
            "time": "08:00",
            "clinicIEN": "198",
            "clinicName": "AUDIOLOGY",
            "clinicStopCode": "403",
            "provider": {"duz": "10000000229", "name": "PROVIDER,TEST"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "60",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "HEARING AID FITTING",
        },
    ],
    # Female Gulf War Veteran
    "100023": [
        {
            "appointmentIEN": "2234567",
            "date": generate_appointment_date(14),
            "time": "10:00",
            "clinicIEN": "196",
            "clinicName": "MENTAL HEALTH CLINIC",
            "clinicStopCode": "502",
            "provider": {"duz": "10000000222", "name": "THOMPSON,MICHELLE K"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "50",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "MST COUNSELING",
        },
        {
            "appointmentIEN": "2234568",
            "date": generate_appointment_date(21),
            "time": "15:00",
            "clinicIEN": "199",
            "clinicName": "WOMEN'S HEALTH CLINIC",
            "clinicStopCode": "322",
            "provider": {"duz": "10000000229", "name": "PROVIDER,TEST"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "30",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "ANNUAL EXAM",
        },
        {
            "appointmentIEN": "2234569",
            "date": generate_appointment_date(-7),
            "time": "13:00",
            "clinicIEN": "195",
            "clinicName": "PRIMARY CARE CLINIC",
            "clinicStopCode": "323",
            "provider": {"duz": "10000000221", "name": "SMITH,JENNIFER A"},
            "status": "NO SHOW",
            "type": "REGULAR",
            "length": "30",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "FOLLOW UP",
        },
    ],
    # OEF/OIF Polytrauma
    "100024": [
        {
            "appointmentIEN": "3234567",
            "date": generate_appointment_date(7),
            "time": "08:30",
            "clinicIEN": "200",
            "clinicName": "ORTHOPEDIC CLINIC",
            "clinicStopCode": "203",
            "provider": {"duz": "10000000230", "name": "MARTINEZ,CARLOS E"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "45",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "PROSTHETIC ADJUSTMENT",
        },
        {
            "appointmentIEN": "3234568",
            "date": generate_appointment_date(7),
            "time": "11:00",
            "clinicIEN": "201",
            "clinicName": "PAIN CLINIC",
            "clinicStopCode": "409",
            "provider": {"duz": "10000000229", "name": "PROVIDER,TEST"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "30",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "PAIN MANAGEMENT",
        },
        {
            "appointmentIEN": "3234569",
            "date": generate_appointment_date(14),
            "time": "14:00",
            "clinicIEN": "196",
            "clinicName": "MENTAL HEALTH CLINIC",
            "clinicStopCode": "502",
            "provider": {"duz": "10000000220", "name": "WILLIAMS,PATRICIA L"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "60",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "PTSD GROUP THERAPY",
        },
        {
            "appointmentIEN": "3234570",
            "date": generate_appointment_date(21),
            "time": "09:00",
            "clinicIEN": "202",
            "clinicName": "REHABILITATION",
            "clinicStopCode": "419",
            "provider": {"duz": "10000000229", "name": "PROVIDER,TEST"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "60",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "PHYSICAL THERAPY",
        },
    ],
    # Elderly Korean War Veteran
    "100025": [
        {
            "appointmentIEN": "4234567",
            "date": generate_appointment_date(3),
            "time": "10:30",
            "clinicIEN": "203",
            "clinicName": "GERIATRICS",
            "clinicStopCode": "324",
            "provider": {"duz": "10000000229", "name": "PROVIDER,TEST"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "45",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "DEMENTIA FOLLOW UP",
        },
        {
            "appointmentIEN": "4234568",
            "date": generate_appointment_date(-14),
            "time": "14:00",
            "clinicIEN": "195",
            "clinicName": "PRIMARY CARE CLINIC",
            "clinicStopCode": "323",
            "provider": {"duz": "10000000221", "name": "SMITH,JENNIFER A"},
            "status": "COMPLETED",
            "type": "REGULAR",
            "length": "30",
            "checkInTime": "13:45",
            "checkOutTime": "14:40",
            "purpose": "ROUTINE FOLLOW UP",
        },
    ],
    # Homeless Veteran
    "100026": [
        {
            "appointmentIEN": "5234567",
            "date": generate_appointment_date(1),
            "time": "13:00",
            "clinicIEN": "204",
            "clinicName": "SUBSTANCE ABUSE CLINIC",
            "clinicStopCode": "511",
            "provider": {"duz": "10000000229", "name": "PROVIDER,TEST"},
            "status": "SCHEDULED",
            "type": "WALK-IN",
            "length": "30",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "SUBSTANCE ABUSE COUNSELING",
        },
        {
            "appointmentIEN": "5234568",
            "date": generate_appointment_date(7),
            "time": "09:00",
            "clinicIEN": "205",
            "clinicName": "SOCIAL WORK SERVICE",
            "clinicStopCode": "125",
            "provider": {"duz": "10000000224", "name": "WILSON,JAMES T"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "60",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "HOUSING ASSISTANCE",
        },
    ],
    # Recent Female Veteran
    "100027": [
        {
            "appointmentIEN": "6234567",
            "date": generate_appointment_date(14),
            "time": "15:30",
            "clinicIEN": "196",
            "clinicName": "MENTAL HEALTH CLINIC",
            "clinicStopCode": "502",
            "provider": {"duz": "10000000222", "name": "THOMPSON,MICHELLE K"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "50",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "INDIVIDUAL THERAPY",
        },
        {
            "appointmentIEN": "6234568",
            "date": generate_appointment_date(30),
            "time": "10:00",
            "clinicIEN": "195",
            "clinicName": "PRIMARY CARE CLINIC",
            "clinicStopCode": "323",
            "provider": {"duz": "10000000221", "name": "SMITH,JENNIFER A"},
            "status": "SCHEDULED",
            "type": "NEW PATIENT",
            "length": "60",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "ESTABLISH CARE",
        },
    ],
    # Rural Veteran with Telehealth
    "100028": [
        {
            "appointmentIEN": "7234567",
            "date": generate_appointment_date(5),
            "time": "11:00",
            "clinicIEN": "590",
            "clinicName": "TELEHEALTH CLINIC",
            "clinicStopCode": "590",
            "provider": {"duz": "10000000221", "name": "SMITH,JENNIFER A"},
            "status": "SCHEDULED",
            "type": "TELEHEALTH",
            "length": "30",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "TELEHEALTH FOLLOW UP",
            "modality": "VIDEO",
        },
        {
            "appointmentIEN": "7234568",
            "date": generate_appointment_date(90),
            "time": "08:00",
            "clinicIEN": "195",
            "clinicName": "PRIMARY CARE CLINIC",
            "clinicStopCode": "323",
            "provider": {"duz": "10000000221", "name": "SMITH,JENNIFER A"},
            "status": "SCHEDULED",
            "type": "REGULAR",
            "length": "30",
            "checkInTime": "",
            "checkOutTime": "",
            "purpose": "ANNUAL PHYSICAL",
        },
    ],
}

# Clinic schedules
CLINIC_SCHEDULES: dict[str, dict[str, any]] = {
    "195": {  # Primary Care
        "name": "PRIMARY CARE CLINIC",
        "stopCode": "323",
        "location": "BUILDING 1, FLOOR 2",
        "phone": "(202) 745-8234",
        "hours": {
            "monday": "08:00-17:00",
            "tuesday": "08:00-17:00",
            "wednesday": "08:00-17:00",
            "thursday": "08:00-17:00",
            "friday": "08:00-17:00",
            "saturday": "CLOSED",
            "sunday": "CLOSED",
        },
        "providers": ["SMITH,JENNIFER A", "GARCIA,MARIA S"],
        "appointmentLength": "30",
        "overbookAllowed": True,
        "maxOverbooks": "2",
    },
    "196": {  # Mental Health
        "name": "MENTAL HEALTH CLINIC",
        "stopCode": "502",
        "location": "BUILDING 2, FLOOR 3",
        "phone": "(202) 745-8345",
        "hours": {
            "monday": "08:00-18:00",
            "tuesday": "08:00-18:00",
            "wednesday": "08:00-18:00",
            "thursday": "08:00-18:00",
            "friday": "08:00-16:00",
            "saturday": "CLOSED",
            "sunday": "CLOSED",
        },
        "providers": ["WILLIAMS,PATRICIA L", "THOMPSON,MICHELLE K", "WILSON,JAMES T"],
        "appointmentLength": "50",
        "overbookAllowed": False,
        "maxOverbooks": "0",
    },
}


def get_appointments_for_patient(dfn: str) -> list[dict[str, any]]:
    """Get appointments for a patient"""
    return PATIENT_APPOINTMENTS.get(dfn, [])


def get_appointments_for_clinic(
    clinic_ien: str, _start_date: str, _end_date: str
) -> list[dict[str, any]]:
    """Get appointments for a clinic within date range"""
    from src.data.test_patients import TEST_PATIENTS

    appointments = []

    # In a real system, this would filter by date range
    for patient_dfn, patient_appts in PATIENT_APPOINTMENTS.items():
        for appt in patient_appts:
            if appt["clinicIEN"] == clinic_ien:
                # Add patient identifier and name to appointment
                appt_copy = appt.copy()
                appt_copy["patientIEN"] = patient_dfn  # Use patientIEN for consistency

                # Get patient name from test patients
                patient = TEST_PATIENTS.get(patient_dfn, {})
                appt_copy["patientName"] = patient.get("name", "UNKNOWN,PATIENT")

                appointments.append(appt_copy)

    return appointments


def get_clinic_info(clinic_ien: str) -> dict[str, any]:
    """Get clinic information"""
    return CLINIC_SCHEDULES.get(
        clinic_ien,
        {
            "name": "UNKNOWN CLINIC",
            "stopCode": "000",
            "location": "UNKNOWN",
            "phone": "(000) 000-0000",
        },
    )
