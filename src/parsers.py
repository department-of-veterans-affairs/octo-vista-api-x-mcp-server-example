"""Parsers for converting Vista RPC responses to structured data"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from .models import (
    Allergy,
    Appointment,
    Gender,
    LabResult,
    Medication,
    PatientDemographics,
    PatientSearchResult,
    Problem,
    Provider,
    VitalSign,
)

logger = logging.getLogger(__name__)


def parse_fileman_date(fm_date: str) -> Optional[str]:
    """
    Convert FileMan date to ISO 8601 format
    
    FileMan format: YYYMMDD.HHMMSS where YYY = Year - 1700
    
    Args:
        fm_date: FileMan date string
        
    Returns:
        ISO 8601 formatted date string or None if invalid
    """
    if not fm_date or fm_date == "0":
        return None
        
    try:
        # Handle date with time
        if "." in fm_date:
            date_part, time_part = fm_date.split(".", 1)
        else:
            date_part = fm_date
            time_part = "000000"
        
        # Parse date
        if len(date_part) >= 7:
            year = int(date_part[:3]) + 1700
            month = int(date_part[3:5])
            day = int(date_part[5:7])
            
            # Parse time
            hour = int(time_part[:2]) if len(time_part) >= 2 else 0
            minute = int(time_part[2:4]) if len(time_part) >= 4 else 0
            second = int(time_part[4:6]) if len(time_part) >= 6 else 0
            
            dt = datetime(year, month, day, hour, minute, second)
            return dt.isoformat()
            
    except (ValueError, IndexError) as e:
        logger.debug(f"Failed to parse FileMan date '{fm_date}': {e}")
        
    return None


def parse_vista_date(date_str: str) -> Optional[str]:
    """
    Parse various Vista date formats
    
    Handles:
    - FileMan dates (YYYMMDD.HHMMSS)
    - MM/DD/YYYY format
    - Other common formats
    
    Args:
        date_str: Date string from Vista
        
    Returns:
        ISO 8601 formatted date string or None
    """
    if not date_str or date_str == "0":
        return None
        
    # Try FileMan format first
    if re.match(r"^\d{7}", date_str):
        return parse_fileman_date(date_str)
        
    # Try MM/DD/YYYY format
    if "/" in date_str:
        try:
            dt = datetime.strptime(date_str.split()[0], "%m/%d/%Y")
            return dt.date().isoformat()
        except:
            pass
            
    # Return original if can't parse
    return date_str


def calculate_age(birth_date: str) -> Optional[int]:
    """Calculate age from birth date"""
    try:
        if birth_date:
            # Parse ISO date
            if "T" in birth_date:
                birth = datetime.fromisoformat(birth_date.split("T")[0])
            else:
                birth = datetime.fromisoformat(birth_date)
            today = datetime.now()
            age = today.year - birth.year
            if (today.month, today.day) < (birth.month, birth.day):
                age -= 1
            return age
    except:
        pass
    return None


def parse_delimited_string(
    data: str, 
    delimiter: str = "^", 
    line_delimiter: str = "\n"
) -> List[List[str]]:
    """
    Parse Vista delimited string format
    
    Args:
        data: Raw delimited string
        delimiter: Field delimiter (default: ^)
        line_delimiter: Line delimiter (default: newline)
        
    Returns:
        List of parsed rows
    """
    if not data or data.strip() == "":
        return []
        
    # Normalize line endings
    data = data.replace("\r\n", "\n").replace("\r", "\n")
    
    # Split into lines
    lines = data.strip().split(line_delimiter)
    
    # Parse each line
    rows = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("~"):  # Skip section headers
            rows.append(line.split(delimiter))
            
    return rows


def parse_patient_name(name: str) -> Tuple[str, str, str]:
    """
    Parse Vista name format (LAST,FIRST MIDDLE)
    
    Args:
        name: Patient name in Vista format
        
    Returns:
        Tuple of (last_name, first_name, middle_name)
    """
    last_name = ""
    first_name = ""
    middle_name = ""
    
    if "," in name:
        parts = name.split(",", 1)
        last_name = parts[0].strip()
        
        if len(parts) > 1:
            name_parts = parts[1].strip().split(" ", 1)
            first_name = name_parts[0]
            if len(name_parts) > 1:
                middle_name = name_parts[1]
                
    return last_name, first_name, middle_name


# Patient Parsers
def parse_patient_search(result: str) -> List[PatientSearchResult]:
    """
    Parse ORWPT LIST response
    
    Format: DFN^NAME^GENDER^DOB^SSN^SENSITIVE_FLAG
    """
    patients = []
    rows = parse_delimited_string(result)
    
    for row in rows:
        if len(row) >= 5:
            try:
                patient = PatientSearchResult(
                    dfn=row[0],
                    name=row[1],
                    gender=row[2] if len(row) > 2 else None,
                    date_of_birth=parse_vista_date(row[3]) if len(row) > 3 else None,
                    ssn_last_four=row[4][-4:] if len(row) > 4 and len(row[4]) >= 4 else "****",
                    sensitive=row[5] == "YES" if len(row) > 5 else False,
                    station="",  # Will be filled by caller
                )
                patients.append(patient)
            except Exception as e:
                logger.error(f"Failed to parse patient row: {row}, error: {e}")
                
    return patients


def parse_patient_demographics(result: str, dfn: str) -> Optional[PatientDemographics]:
    """
    Parse ORWPT ID INFO response
    
    Multi-line format with demographics, address, contacts
    """
    if not result:
        return None
        
    lines = result.strip().split("\n")
    if not lines:
        return None
        
    # Parse first line: DFN^NAME^SSN^DOB^AGE^SEX^^SERVICE_CONNECTED^SENSITIVE^TYPE
    first_line = lines[0].split("^")
    if len(first_line) < 6:
        return None
        
    # Parse name
    last_name, first_name, middle_name = parse_patient_name(first_line[1])
    
    # Parse birth date and calculate age
    birth_date = parse_vista_date(first_line[3]) if len(first_line) > 3 else None
    age = calculate_age(birth_date) if birth_date else None
    
    demographics = PatientDemographics(
        dfn=dfn,
        name=first_line[1],
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        ssn=f"***-**-{first_line[2][-4:]}" if len(first_line[2]) >= 4 else "***-**-****",
        date_of_birth=birth_date or first_line[3],
        age=age or (int(first_line[4]) if len(first_line) > 4 and first_line[4].isdigit() else None),
        gender=first_line[5] if len(first_line) > 5 else None,
        station="",  # Will be filled by caller
    )
    
    # Parse additional lines for address, phone, etc.
    address_data = {}
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("ADDRESS:"):
            # Parse address
            addr_parts = line.replace("ADDRESS:", "").strip().split("^")
            if addr_parts:
                address_data["street"] = addr_parts[0].strip()
                if len(addr_parts) > 2:
                    address_data["city"] = addr_parts[2]
                if len(addr_parts) > 3:
                    address_data["state"] = addr_parts[3]
                if len(addr_parts) > 4:
                    address_data["zip"] = addr_parts[4]
                    
        elif line.startswith("PHONE:"):
            # Parse phone numbers
            phone_parts = line.replace("PHONE:", "").strip().split("^")
            if phone_parts:
                demographics.phone = phone_parts[0].strip()
            if len(phone_parts) > 1 and "CELL:" in phone_parts[1]:
                demographics.cell_phone = phone_parts[1].replace("CELL:", "").strip()
                
        elif line.startswith("NOK:") or line.startswith("EMERGENCY:"):
            # Parse emergency contact
            if not demographics.emergency_contact:
                demographics.emergency_contact = {}
            contact_parts = line.split("^")
            if contact_parts:
                demographics.emergency_contact["name"] = contact_parts[0].split(":")[-1].strip()
                if len(contact_parts) > 1:
                    demographics.emergency_contact["phone"] = contact_parts[1]
                if len(contact_parts) > 2:
                    demographics.emergency_contact["relationship"] = contact_parts[2]
                    
    if address_data:
        demographics.address = address_data
        
    return demographics


# Clinical Parsers
def parse_medications(result: str) -> List[Medication]:
    """
    Parse ORWPS ACTIVE response
    
    Format: ~Active Medications
    ID^NAME^SIG^START_DATE^STOP_DATE^QTY^REFILLS^STATUS
    """
    medications = []
    rows = parse_delimited_string(result)
    
    for row in rows:
        if len(row) >= 3 and not row[0].startswith("~"):
            try:
                med = Medication(
                    id=row[0] if row[0] else None,
                    name=row[1],
                    sig=row[2],
                    start_date=parse_fileman_date(row[3]) if len(row) > 3 and row[3] else None,
                    stop_date=parse_fileman_date(row[4]) if len(row) > 4 and row[4] else None,
                    quantity=row[5] if len(row) > 5 else None,
                    refills=int(row[6]) if len(row) > 6 and row[6].isdigit() else None,
                    status="ACTIVE" if len(row) > 7 and row[7] == "Y" else "INACTIVE",
                )
                medications.append(med)
            except Exception as e:
                logger.error(f"Failed to parse medication row: {row}, error: {e}")
                
    return medications


def parse_lab_results(result: str) -> List[LabResult]:
    """
    Parse ORWLRR INTERIM response
    
    Format: ~Lab Results
    ID^TEST_NAME^VALUE^UNITS^REF_RANGE^DATE_TIME^FLAG^STATUS
    """
    lab_results = []
    rows = parse_delimited_string(result)
    
    for row in rows:
        if len(row) >= 6 and not row[0].startswith("~"):
            try:
                lab = LabResult(
                    id=row[0] if row[0] else None,
                    test_name=row[1],
                    value=row[2],
                    units=row[3] if len(row) > 3 else None,
                    reference_range=row[4] if len(row) > 4 else None,
                    date_time=parse_fileman_date(row[5]) if row[5] else datetime.now().isoformat(),
                    flag=row[6] if len(row) > 6 else None,
                    status=row[7] if len(row) > 7 else "F",  # F=Final
                )
                lab_results.append(lab)
            except Exception as e:
                logger.error(f"Failed to parse lab result row: {row}, error: {e}")
                
    return lab_results


def parse_vital_signs(result: str) -> List[VitalSign]:
    """
    Parse ORQQVI VITALS response
    
    Format: ~Vital Signs
    DATE_TIME^TYPE^VALUE^UNITS^QUALIFIERS
    """
    vital_signs = []
    rows = parse_delimited_string(result)
    
    for row in rows:
        if len(row) >= 3 and not row[0].startswith("~"):
            try:
                vital = VitalSign(
                    date_time=parse_fileman_date(row[0]) if row[0] else datetime.now().isoformat(),
                    type=row[1],
                    value=row[2],
                    units=row[3] if len(row) > 3 else None,
                    qualifiers=row[4] if len(row) > 4 else None,
                )
                vital_signs.append(vital)
            except Exception as e:
                logger.error(f"Failed to parse vital sign row: {row}, error: {e}")
                
    return vital_signs


def parse_problems(result: str) -> List[Problem]:
    """
    Parse ORQQPL PROBLEM LIST response
    
    Format: ID^IEN^DESCRIPTION^ICD_CODE^STATUS^DATE_ENTERED^TYPE
    """
    problems = []
    rows = parse_delimited_string(result)
    
    for row in rows:
        if len(row) >= 3:
            try:
                # Extract ICD code from description if embedded
                icd_code = None
                description = row[2]
                if "ICD-" in description:
                    match = re.search(r"ICD-\d+:\s*([A-Z0-9.]+)", description)
                    if match:
                        icd_code = match.group(1)
                        
                problem = Problem(
                    id=row[0],
                    snomed_code=row[1].replace("S:", "") if len(row) > 1 and row[1].startswith("S:") else None,
                    description=description,
                    icd_code=icd_code or (row[3] if len(row) > 3 else None),
                    status=row[4] if len(row) > 4 else "ACTIVE",
                    onset_date=parse_fileman_date(row[5]) if len(row) > 5 and row[5] else None,
                    type=row[6] if len(row) > 6 else None,
                )
                problems.append(problem)
            except Exception as e:
                logger.error(f"Failed to parse problem row: {row}, error: {e}")
                
    return problems


def parse_allergies(result: str) -> List[Allergy]:
    """
    Parse ORQQAL LIST response
    
    Format: ID^AGENT^TYPE^DATE^REACTIONS^SEVERITY^VERIFIED
    """
    allergies = []
    rows = parse_delimited_string(result)
    
    for row in rows:
        if len(row) >= 2:
            try:
                # Parse reactions (may be semicolon-separated)
                reactions = []
                if len(row) > 4 and row[4]:
                    reactions = [r.strip() for r in row[4].split(";")]
                    
                allergy = Allergy(
                    id=row[0] if row[0] else None,
                    agent=row[1],
                    type=row[2] if len(row) > 2 else None,
                    date_entered=parse_fileman_date(row[3]) if len(row) > 3 and row[3] else None,
                    reactions=reactions,
                    severity=row[5] if len(row) > 5 else None,
                    verified=row[6] == "VERIFIED" if len(row) > 6 else False,
                )
                allergies.append(allergy)
            except Exception as e:
                logger.error(f"Failed to parse allergy row: {row}, error: {e}")
                
    return allergies


# Administrative Parsers
def parse_appointments(result: Union[str, Dict]) -> List[Appointment]:
    """
    Parse SDES GET APPTS BY CLIN IEN 2 response
    
    Can be JSON or delimited format
    """
    appointments = []
    
    # Handle JSON response
    if isinstance(result, dict):
        if "appointments" in result:
            for appt in result["appointments"]:
                try:
                    appointment = Appointment(
                        appointment_ien=appt.get("appointmentIEN", ""),
                        patient_ien=appt.get("patientIEN", ""),
                        patient_name=appt.get("patientName", ""),
                        date_time=appt.get("dateTime", ""),
                        clinic_ien=appt.get("clinicIEN", ""),
                        clinic_name=appt.get("clinicName", ""),
                        status=appt.get("status", ""),
                        provider=appt.get("provider"),
                        check_in_time=appt.get("checkInTime"),
                        check_out_time=appt.get("checkOutTime"),
                    )
                    appointments.append(appointment)
                except Exception as e:
                    logger.error(f"Failed to parse appointment: {appt}, error: {e}")
                    
    # Handle delimited response
    elif isinstance(result, str):
        rows = parse_delimited_string(result)
        for row in rows:
            if len(row) >= 6:
                try:
                    appointment = Appointment(
                        appointment_ien=row[0],
                        patient_ien=row[1],
                        patient_name=row[2],
                        date_time=parse_fileman_date(row[3]) if row[3] else "",
                        clinic_ien=row[4] if len(row) > 4 else "",
                        clinic_name=row[5] if len(row) > 5 else "",
                        status=row[6] if len(row) > 6 else "SCHEDULED",
                    )
                    appointments.append(appointment)
                except Exception as e:
                    logger.error(f"Failed to parse appointment row: {row}, error: {e}")
                    
    return appointments


def parse_user_info(result: Union[str, Dict], duz: str) -> Optional[Provider]:
    """
    Parse user information from various RPCs
    
    Handles both JSON and delimited formats
    """
    if not result:
        return None
        
    # Handle JSON response
    if isinstance(result, dict):
        return Provider(
            duz=result.get("duz", duz),
            name=result.get("name", ""),
            title=result.get("title"),
            service=result.get("service"),
            phone=result.get("phone"),
            email=result.get("email"),
            role=result.get("role"),
            station=result.get("station"),
        )
        
    # Handle delimited response (ORWU USERINFO format)
    # Format: DUZ^NAME^TITLE^SERVICE^PHONE
    elif isinstance(result, str):
        parts = result.strip().split("^")
        if len(parts) >= 2:
            return Provider(
                duz=parts[0] if parts[0] else duz,
                name=parts[1],
                title=parts[2] if len(parts) > 2 else None,
                service=parts[3] if len(parts) > 3 else None,
                phone=parts[4] if len(parts) > 4 else None,
            )
            
    return None