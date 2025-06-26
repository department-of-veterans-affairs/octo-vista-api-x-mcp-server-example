"""MCP Prompts for Vista API workflows"""

import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_prompts(mcp: FastMCP):
    """Register MCP prompts with the server"""

    @mcp.prompt()
    async def patient_summary(
        patient_dfn: str,
        station: str | None = None,
    ) -> str:
        """
        Generate a comprehensive patient summary workflow

        Args:
            patient_dfn: Patient's DFN to summarize
            station: Vista station number (optional)
        """
        station_param = f', station="{station}"' if station else ""

        return f"""Please provide a comprehensive clinical summary for patient DFN {patient_dfn}:

1. First, get the patient's demographics to understand who they are:
   - Use get_patient_demographics(patient_dfn="{patient_dfn}"{station_param})

2. Retrieve their clinical data:
   - Get active medications: get_medications(patient_dfn="{patient_dfn}"{station_param})
   - Get recent vital signs: get_vital_signs(patient_dfn="{patient_dfn}"{station_param})
   - Get recent lab results: get_lab_results(patient_dfn="{patient_dfn}"{station_param}, days_back=30)
   - Get active problems: get_problems(patient_dfn="{patient_dfn}"{station_param})
   - Get allergies: get_allergies(patient_dfn="{patient_dfn}"{station_param})

3. Analyze the data and provide:
   - Patient overview (age, key demographics)
   - Active medical conditions
   - Current medications with any concerns
   - Recent vital signs trends
   - Notable lab results
   - Allergy alerts
   - Clinical recommendations or areas of concern

Please organize the summary in a clear, clinical format suitable for healthcare providers."""

    @mcp.prompt()
    async def medication_review(
        patient_dfn: str,
        station: str | None = None,
    ) -> str:
        """
        Generate a medication safety review workflow

        Args:
            patient_dfn: Patient's DFN for medication review
            station: Vista station number (optional)
        """
        station_param = f', station="{station}"' if station else ""

        return f"""Please perform a comprehensive medication review for patient DFN {patient_dfn}:

1. Get patient context:
   - Demographics: get_patient_demographics(patient_dfn="{patient_dfn}"{station_param})
   - Active problems: get_problems(patient_dfn="{patient_dfn}"{station_param})
   - Allergies: get_allergies(patient_dfn="{patient_dfn}"{station_param})

2. Get current medications:
   - Use get_medications(patient_dfn="{patient_dfn}"{station_param})

3. Review recent lab results that may affect medications:
   - Use get_lab_results(patient_dfn="{patient_dfn}"{station_param}, days_back=30)
   - Focus on renal function, liver function, and drug levels

4. Perform medication safety analysis:
   - Check for allergy conflicts
   - Identify potential drug interactions
   - Assess dosing appropriateness for age and conditions
   - Look for duplicate therapy
   - Consider renal/hepatic adjustments
   - Identify high-risk medications

5. Provide recommendations:
   - Medications that may need adjustment
   - Potential deprescribing opportunities
   - Monitoring requirements
   - Patient education needs"""

    @mcp.prompt()
    async def clinical_workflow(
        workflow_type: str = "assessment",
    ) -> str:
        """
        Generate a standard clinical workflow

        Args:
            workflow_type: Type of workflow (assessment, admission, discharge)
        """
        workflows = {
            "assessment": """For a comprehensive clinical assessment:

1. Patient identification:
   - Search for patient: search_patients(search_term="ANDERSON")
   - Select patient: select_patient(patient_dfn="100022")

2. Gather comprehensive data:
   - Demographics: get_patient_demographics(patient_dfn="100022")
   - All clinical data: get_patient_data(patient_dfn="100022", domains=["med", "lab", "vital", "problem", "allergy"])

3. Review current status:
   - Recent activity
   - Medication compliance
   - Lab trends
   - Vital sign patterns

4. Document findings and plan""",
            "admission": """For patient admission workflow:

1. Verify patient identity
2. Get comprehensive medical history
3. Review current medications for reconciliation
4. Check allergies and alerts
5. Order admission labs and vitals
6. Document admission note""",
            "discharge": """For patient discharge workflow:

1. Review hospital course
2. Reconcile discharge medications
3. Review pending labs/results
4. Prepare discharge instructions
5. Schedule follow-up appointments
6. Complete discharge summary""",
        }

        return workflows.get(workflow_type, workflows["assessment"])

    @mcp.prompt()
    async def appointment_schedule(
        clinic_ien: str = "195",
        station: str | None = None,
    ) -> str:
        """
        Generate appointment management workflow

        Args:
            clinic_ien: Clinic IEN (default: 195 - Primary Care)
            station: Vista station number (optional)
        """
        station_param = f', station="{station}"' if station else ""

        return f"""To manage appointments for clinic {clinic_ien}:

1. Get current appointment schedule:
   - Use get_appointments(clinic_ien="{clinic_ien}"{station_param})

2. For each appointment, you can:
   - Review patient information: get_patient_demographics(patient_dfn="DFN")
   - Check recent visits and no-shows
   - Review care gaps

3. Appointment management options:
   - Identify available slots
   - Review appointment types
   - Check provider schedules

4. For specific patient scheduling:
   - Search patient: search_patients(search_term="NAME")
   - Review their care needs
   - Find appropriate appointment slot"""

    @mcp.prompt()
    async def geriatric_assessment(
        patient_dfn: str,
        station: str | None = None,
    ) -> str:
        """
        Generate a geriatric assessment workflow

        Args:
            patient_dfn: Elderly patient's DFN
            station: Vista station number (optional)
        """
        station_param = f', station="{station}"' if station else ""

        return f"""Please perform a comprehensive geriatric assessment for patient DFN {patient_dfn}:

1. Get patient overview:
   - Demographics: get_patient_demographics(patient_dfn="{patient_dfn}"{station_param})
   - Confirm age ≥ 65 years

2. Assess key geriatric domains:
   
   a) Polypharmacy risk:
      - Get medications: get_medications(patient_dfn="{patient_dfn}"{station_param})
      - Look for ≥ 5 medications
      - Identify potentially inappropriate medications (Beers Criteria)
      - Check for anticholinergic burden
   
   b) Fall risk factors:
      - Review problems for: fall history, gait disorders, neuropathy
      - Check medications for: sedatives, antihypertensives, psychotropics
      - Review recent vitals for orthostatic changes
   
   c) Cognitive concerns:
      - Look for dementia or cognitive impairment diagnoses
      - Review medications affecting cognition
   
   d) Functional status:
      - Review problems for functional limitations
      - Check for assistive device needs

3. Laboratory monitoring:
   - Get recent labs: get_lab_results(patient_dfn="{patient_dfn}"{station_param}, days_back=90)
   - Check: renal function, B12, thyroid, vitamin D

4. Provide geriatric-specific recommendations:
   - Medication optimization opportunities
   - Fall prevention strategies
   - Cognitive protection measures
   - Care coordination needs"""

    @mcp.prompt()
    async def mental_health_screening() -> str:
        """Generate a mental health screening workflow"""

        return """For mental health screening and assessment:

1. Patient identification and rapport building:
   - Search and select patient
   - Review demographics for age, gender, veteran status

2. Screen for common conditions:
   - Depression (PHQ-9 questions)
   - Anxiety (GAD-7 questions)
   - PTSD (PC-PTSD-5 for veterans)
   - Substance use (AUDIT-C for alcohol)
   - Suicidal ideation

3. Review relevant history:
   - Current psychiatric medications
   - Previous mental health diagnoses
   - Recent psychiatric hospitalizations
   - Current stressors

4. Check for medical contributors:
   - Thyroid function
   - Vitamin deficiencies
   - Chronic pain
   - Sleep disorders

5. Assessment and plan:
   - Severity assessment
   - Safety evaluation
   - Treatment recommendations
   - Referral needs
   - Follow-up planning"""
