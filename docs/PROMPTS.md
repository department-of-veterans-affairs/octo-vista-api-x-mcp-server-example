# Example Prompts

A collection of example prompts for interacting with the Vista API MCP Server through LLM clients. All prompts use actual test data values that work with the mock server.

> **Note**: These are natural language examples for users to type. For pre-defined MCP workflow prompts that guide complex multi-step processes, see the registered prompts in the MCP server (e.g., `/patient_summary`, `/medication_review`).

## Getting Started Prompts

### System Status

- "Is the Vista system available?"
- "Check the connection to Vista"
- "What's the current server time?"
- "Show me the Vista server version"

### Understanding Capabilities

- "What tools do you have available?"
- "What kind of patient data can you access?"
- "Show me what clinical information you can retrieve"

## Patient Search Prompts

### Basic Search with Actual Test Data

- "Search for patients with last name ANDERSON"
- "Find patients whose last name starts with 'MART'"
- "Look for patient GARCIA,ANTONIO"
- "Search for patient with SSN ending in 1234"
- "Find all patients with last name THOMPSON"

### Using Patient IDs

- "Get demographics for patient 100022"
- "Show me information about patient 100023"
- "Select patient 100024"
- "Look up patient DFN 100025"

## Clinical Data Prompts

### Medications with Real Patient IDs

- "Show me medications for patient 100022"
- "What medications is ANDERSON,JAMES taking?"
- "List all medications for patient 100023"
- "Show both active and inactive medications for patient 100024"
- "Get medications for Maria Martinez (100023)"

### Laboratory Results

- "Get lab results for patient 100022 from the last 30 days"
- "Show me recent labs for patient 100023"
- "What are the last 90 days of lab results for patient 100024?"
- "Display lab results for patient 100025 from the past week"
- "Show all labs for patient 100026"

### Vital Signs

- "Get vital signs for patient 100022"
- "Show vitals for ANDERSON,JAMES"
- "What are the current vital signs for patient 100023?"
- "Display vitals for patient 100024"
- "Get vital measurements for patient 100025"

### Problems & Diagnoses

- "List active problems for patient 100022"
- "What problems does patient 100023 have?"
- "Show all problems for patient 100024 including inactive ones"
- "Get the problem list for patient 100025"
- "Display active conditions for patient 100026"

### Allergies

- "Check allergies for patient 100022"
- "What allergies does patient 100023 have?"
- "Show all allergies for patient 100024"
- "List allergies and reactions for patient 100025"
- "Check if patient 100026 has any drug allergies"

## Administrative Prompts

### Appointments

- "Show appointments for clinic 195"
- "Get appointments for primary care clinic"
- "Display today's appointments for clinic 195"
- "Show appointments for the next 7 days"
- "List all appointments for this week"

### User Information

- "Get my user profile"
- "Show user profile for DUZ 10000000219"
- "What's my current user info?"
- "Display information for user 10000000220"
- "Show profile for Dr. Susan Chen"

### Team Members

- "List all team members"
- "Show the care team"
- "Who are the team members at station 500?"
- "Display all providers in the team"

## Complex Clinical Queries

### Comprehensive Patient Review

- "Get patient data for 100022 including medications, labs, vitals, and problems"
- "Show comprehensive data for patient 100023 with all clinical domains"
- "Get patient 100024's data for vital signs, medications, and allergies"
- "Display full clinical data for patient 100025"

### Multi-Domain Queries

- "Get patient 100022's medications and recent labs"
- "Show vitals and problems for patient 100023"
- "Display allergies and medications for patient 100024"
- "Get labs and vital signs for patient 100025"

### Date-Ranged Queries

- "Get lab results for patient 100022 from the last 60 days"
- "Show medications that were active for patient 100023"
- "Get vital signs and labs for patient 100024 from the past month"
- "Display all clinical data for patient 100025 from the last week"

## Workflow Examples with Real Data

### New Patient Review

1. "Search for patient ANDERSON"
2. "Get demographics for patient 100022"
3. "Check allergies for patient 100022"
4. "Show medications for patient 100022"
5. "List active problems for patient 100022"
6. "Get vital signs for patient 100022"

### Medication Review

1. "Show medications for patient 100023"
2. "Check allergies for patient 100023"
3. "Get active problems for patient 100023"
4. "Show recent labs for patient 100023"

### Pre-Visit Check

1. "Select patient 100024"
2. "Get vital signs for patient 100024"
3. "Show active problems for patient 100024"
4. "List medications for patient 100024"
5. "Check recent labs for patient 100024 from last 30 days"

### Clinical Summary

1. "Get patient data for 100025 including med, lab, vital, problem, and allergy domains"
2. "Show demographics for patient 100025"
3. "List team members"

## Test Data Quick Reference

### Available Test Patients

- **100022** - ANDERSON,JAMES ROBERT (Vietnam Era, PTSD)
- **100023** - MARTINEZ,MARIA ELENA (Female Gulf War Vet)
- **100024** - THOMPSON,MICHAEL DAVID (OEF/OIF, Polytrauma)
- **100025** - WILLIAMS,ROBERT EARL (Elderly Korean War Vet)
- **100026** - JOHNSON,DAVID WAYNE (Homeless Veteran)
- **100027** - DAVIS,JENNIFER LYNN (Recent Female Veteran)
- **100028** - WILSON,GEORGE HENRY (Rural Veteran)
- **100029** - GARCIA,ANTONIO JOSE (Complex Medical Needs)

### Test Stations

- **500** - Washington DC VAMC (primary)
- **508** - Atlanta VAMC
- **640** - Palo Alto VAMC

### Test Users

- **10000000219** - Dr. Susan Chen (primary test user)
- **10000000220** - Dr. John Smith
- **10000000221** - Dr. Emily Williams

### Test Clinics

- **195** - Primary Care Clinic (default)

## Tips for Effective Prompts

### Use Specific Patient IDs

- ❌ "Show medications"
- ✅ "Show medications for patient 100022"

### Include Proper Parameters

- ❌ "Get labs"
- ✅ "Get lab results for patient 100023 from the last 30 days"

### Use Correct Patient Identifiers

- ✅ "Patient 100022" (DFN)
- ✅ "ANDERSON,JAMES" (name from search)
- ❌ "Patient Smith" (too vague)

### Specify Data Domains Correctly

- ✅ "Get patient data for 100024 with domains: med, lab, vital"
- ✅ "Show medications, problems, and allergies for patient 100025"
- ❌ "Get everything for the patient"

## Natural Language Variations

The MCP server understands various phrasings:

### For Patient IDs

- "Patient 100022"
- "DFN 100022"
- "Patient with ID 100022"
- "Patient number 100022"

### For Medications

- "medications"
- "meds"
- "prescriptions"
- "drugs"
- "active medications only"
- "all medications including inactive"

### For Lab Results

- "lab results"
- "labs"
- "laboratory values"
- "test results"
- "bloodwork"