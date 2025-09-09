"""Tests for medication model"""

from datetime import datetime

from src.models.patient.medication import Medication


class TestMedicationModel:
    """Test Medication model functionality"""

    def test_medication_creation_basic(self):
        """Test creating a basic medication instance"""
        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "name": "METFORMIN TAB",
            "qualifiedName": "METFORMIN 1000MG TAB",
            "medType": "urn:sct:73639000",
            "productFormName": "TAB",
            "medStatus": "urn:sct:73425007",
            "medStatusName": "active",
            "vaStatus": "ACTIVE",
            "vaType": "O",
            "type": "Prescription",
            "sig": "TAKE 1 TABLET BY MOUTH TWICE DAILY",
            "patientInstruction": "Take with meals",
            "facilityCode": "500",
            "facilityName": "TEST FACILITY",
            "overallStart": datetime(2024, 1, 1),
            "lastFilled": datetime(2024, 1, 1),
            "dosages": [
                {
                    "dose": "1000 MG",
                    "routeName": "PO",
                    "scheduleName": "BID",
                    "units": "MG",
                    "doseForm": "TAB",
                }
            ],
            "orders": [],
            "fills": [],
            "isActive": True,
            "isInpatient": False,
            "isOutpatient": True,
        }

        medication = Medication.model_validate(med_data)

        assert medication.name == "METFORMIN TAB"
        assert medication.qualified_name == "METFORMIN 1000MG TAB"
        assert medication.med_type == "urn:sct:73639000"
        assert medication.va_status == "ACTIVE"
        assert medication.va_type == "O"
        assert medication.type == "Prescription"
        assert medication.sig == "TAKE 1 TABLET BY MOUTH TWICE DAILY"
        assert medication.patient_instruction == "Take with meals"
        assert medication.is_active is True
        assert medication.dose == "1000 MG"
        assert medication.route == "PO"

    def test_medication_with_orders_and_fills(self):
        """Test medication with orders and fills"""
        med_data = {
            "uid": "urn:va:med:500:123:789",
            "localId": "789",
            "name": "LISINOPRIL TAB",
            "qualifiedName": "LISINOPRIL 20MG TAB",
            "medType": "urn:sct:73639000",
            "productFormName": "TAB",
            "medStatus": "urn:sct:73425007",
            "medStatusName": "active",
            "vaStatus": "ACTIVE",
            "vaType": "O",
            "type": "Prescription",
            "sig": "TAKE 1 TABLET DAILY",
            "patientInstruction": "Take in the morning",
            "facilityCode": "500",
            "facilityName": "TEST FACILITY",
            "overallStart": datetime(2024, 2, 1),
            "lastFilled": datetime(2024, 3, 1),
            "isActive": True,
            "isInpatient": False,
            "isOutpatient": True,
            "dosages": [
                {
                    "dose": "20 MG",
                    "routeName": "PO",
                    "scheduleName": "QD",
                    "units": "MG",
                    "doseForm": "TAB",
                }
            ],
            "orders": [
                {
                    "daysSupply": 30,
                    "fillCost": 5.00,
                    "fillsAllowed": 11,
                    "fillsRemaining": 10,
                    "locationName": "PRIMARY CARE",
                    "locationUid": "urn:va:location:500:23",
                    "orderUid": "urn:va:order:500:123:789",
                    "ordered": datetime(2024, 2, 1, 8, 0, 0),
                    "pharmacistName": "PHARMACIST,ONE",
                    "pharmacistUid": "urn:va:user:500:1234",
                    "prescriptionId": 123456,
                    "providerName": "PROVIDER,ONE",
                    "providerUid": "urn:va:user:500:5678",
                    "quantityOrdered": 30,
                    "vaRouting": "W",
                    "status": "ACTIVE",
                    "statusName": "Active",
                    "expirationDate": datetime(2025, 2, 1),
                    "refillsRemaining": 10,
                }
            ],
            "fills": [
                {
                    "daysSupplyDispensed": 30,
                    "dispenseDate": datetime(2024, 2, 1),
                    "quantityDispensed": 30,
                    "releaseDate": datetime(2024, 2, 1),
                    "routing": "W",
                    "fillNumber": 1,
                    "pharmacyName": "MAIN PHARMACY",
                    "pharmacyUid": "urn:va:location:500:23",
                    "prescriptionId": 123456,
                    "status": "FILLED",
                    "statusName": "Filled",
                }
            ],
        }

        medication = Medication.model_validate(med_data)

        assert len(medication.orders) == 1
        assert medication.orders[0].prescription_id == "123456"
        assert medication.orders[0].provider_name == "PROVIDER,ONE"
        assert len(medication.fills) == 1
        assert medication.fills[0].quantity_dispensed == 30
        assert medication.fills[0].routing == "W"

    def test_medication_discontinued_status(self):
        """Test discontinued medication handling"""
        med_data = {
            "uid": "urn:va:med:500:123:456",
            "localId": "456",
            "name": "WARFARIN TAB",
            "qualifiedName": "WARFARIN 5MG TAB",
            "medType": "urn:sct:73639000",
            "productFormName": "TAB",
            "medStatus": "urn:sct:385669000",
            "medStatusName": "inactive",
            "vaStatus": "DISCONTINUED",
            "vaType": "O",
            "type": "Prescription",
            "sig": "TAKE AS DIRECTED",
            "patientInstruction": "",
            "facilityCode": "500",
            "facilityName": "TEST FACILITY",
            "overallStart": datetime(2023, 12, 1),
            "overallStop": datetime(2024, 3, 1),
            "lastFilled": datetime(2024, 2, 1),
            "stopped": datetime(2024, 3, 1),
            "isActive": False,
            "isInpatient": False,
            "isOutpatient": True,
            "dosages": [
                {
                    "dose": "5 MG",
                    "routeName": "PO",
                    "scheduleName": "DAILY",
                    "units": "MG",
                    "doseForm": "TAB",
                }
            ],
            "orders": [],
            "fills": [],
        }

        medication = Medication.model_validate(med_data)

        assert medication.is_active is False
        assert medication.va_status == "DISCONTINUED"
        assert medication.stopped is not None
        assert medication.dose == "5 MG"
        assert medication.route == "PO"
