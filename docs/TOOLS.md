# Vista API MCP Tools Reference

Complete reference for all tools available in the Vista API MCP server.

## Patient Tools

### search_patients
Search for patients by name or SSN fragment.

**Parameters:**
- `search_text` (required): Name or SSN fragment (min 3 chars)
- `max_results`: Maximum results to return (default: 10)

**Returns:** List of matching patients with ID, name, SSN, DOB

**Example:**
```
search_text: "SMITH"
Returns: [{"id": "100023", "name": "SMITH,MARY", "ssn": "***-**-2222", "dob": "08/22/1975"}]
```

### get_patient_demographics
Get detailed demographic information for a specific patient.

**Parameters:**
- `patient_id` (required): Patient ID (DFN/IEN)

**Returns:** Full demographics including address, phone, emergency contact, insurance

### select_patient
Set the active patient context for subsequent operations.

**Parameters:**
- `patient_id` (required): Patient ID to select

**Returns:** Confirmation with patient name

### get_patient_data
Retrieve comprehensive patient data from VPR (Virtual Patient Record).

**Parameters:**
- `patient_id` (required): Patient ID
- `domain`: Specific domain (optional) - vital, med, problem, allergy, lab, document
- `start_date`: Start date for data range (optional)
- `end_date`: End date for data range (optional)

**Returns:** Complete patient data in requested domains

### get_patient_clinical_summary
Get a comprehensive clinical summary combining all patient data.

**Parameters:**
- `patient_id` (required): Patient ID

**Returns:** Structured summary with demographics, problems, medications, allergies, recent labs, vitals

## Clinical Tools

### get_medications
Retrieve patient medications (active and inactive).

**Parameters:**
- `patient_id` (required): Patient ID
- `status`: Filter by status - "active", "inactive", "all" (default: "active")

**Returns:** List of medications with name, dosage, schedule, status, prescriber

### get_lab_results
Get laboratory test results.

**Parameters:**
- `patient_id` (required): Patient ID
- `days_back`: Number of days to look back (default: 30)
- `test_name`: Filter by specific test name (optional)

**Returns:** Lab results with test names, values, reference ranges, flags

### get_vital_signs
Retrieve vital signs measurements.

**Parameters:**
- `patient_id` (required): Patient ID
- `days_back`: Number of days to look back (default: 30)
- `vital_type`: Filter by type - bp, pulse, temp, resp, weight, height, bmi, pain (optional)

**Returns:** Vital signs with timestamps and values

### get_problems
Get patient problem list.

**Parameters:**
- `patient_id` (required): Patient ID
- `status`: Filter - "active", "inactive", "all" (default: "active")

**Returns:** Problems with ICD codes, descriptions, onset dates, status

### get_allergies
Retrieve patient allergies and adverse reactions.

**Parameters:**
- `patient_id` (required): Patient ID

**Returns:** Allergies with allergen, reaction type, severity, observed/historical

### get_notes
Get clinical notes and documents.

**Parameters:**
- `patient_id` (required): Patient ID
- `days_back`: Number of days to look back (default: 90)
- `note_type`: Filter by type (optional)

**Returns:** List of notes with titles, authors, dates; full text on request

### get_orders
Retrieve clinical orders.

**Parameters:**
- `patient_id` (required): Patient ID
- `status`: Filter - "active", "completed", "all" (default: "active")

**Returns:** Orders with type, status, ordering provider, dates

## Administrative Tools

### get_appointments
Get patient appointments.

**Parameters:**
- `patient_id` (required): Patient ID
- `start_date`: Start of date range (default: today)
- `end_date`: End of date range (default: 90 days)
- `include_past`: Include past appointments (default: false)

**Returns:** Appointments with clinic, provider, date/time, status

### get_user_profile
Retrieve user profile information.

**Parameters:**
- `duz`: User DUZ (optional, defaults to current user)

**Returns:** User name, title, service, phone, email, roles

### list_team_members
List members of a patient's care team.

**Parameters:**
- `patient_id` (required): Patient ID

**Returns:** Team members with roles, names, contact information

### get_clinic_list
Get list of available clinics.

**Parameters:**
- `search_text`: Filter clinics by name (optional)

**Returns:** Clinics with names, locations, phone numbers

## System Tools

### heartbeat
Keep connection alive and check server status.

**Returns:** Server status and timestamp

### get_server_time
Get current Vista server date and time.

**Returns:** Server date/time in both FileMan and readable formats

### get_intro_message
Get system intro/welcome message.

**Returns:** System welcome message and announcements

### get_user_info
Get current user context information.

**Returns:** Current user DUZ, name, station

### get_server_version
Get Vista server version information.

**Returns:** Vista version, patch level, site information

## Tool Usage Notes

### Authentication
All tools require proper authentication through Vista API X. The MCP server handles token management automatically.

### Patient Context
Some tools work better after calling `select_patient` to establish context, though most accept explicit patient_id parameters.

### Error Handling
Tools return structured errors for:
- Invalid patient IDs
- Insufficient permissions
- Missing required data
- Connection issues

### Performance
- Use date ranges to limit data volume
- Cache frequently accessed data when appropriate
- Some operations may take longer with large datasets

### Data Formats
- Dates: Accept various formats, returned as ISO 8601
- IDs: Patient IDs are DFN/IEN values
- Status values: Standardized across tools (active/inactive/completed)