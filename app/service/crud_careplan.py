# app/crud.py
import uuid
from datetime import datetime

from app.service.crud_doctor_availabilty import get_doctor_by_specialty
from app.utils.ai_agent import assign_slot_to_appointment
from ..database import db

CAREPLANS_COLL = "careplans"

async def get_careplan_by_appointment_id(appointment_id: str):
    """
    Returns (careplan, appointment) given an appointment ID
    """
    doc = await db[CAREPLANS_COLL].find_one({"appointments.id": appointment_id})
    if not doc:
        return None, None
    
    appointment = next((a for a in doc["appointments"] if a["id"] == appointment_id), None)
    return doc, appointment

async def create_careplan(careplan: dict) -> dict:
    careplan["created_at"] = datetime.utcnow()
    res = await db[CAREPLANS_COLL].insert_one(careplan)
    careplan["_id"] = str(res.inserted_id)

    if "patient_id" in careplan:
        patient_id = careplan["patient_id"]

        if "appointments" in careplan and careplan["appointments"]:
            for appt in careplan["appointments"]:
                if appt["status"] == "pending":
                    # 🔹 Try to find a doctor by matching specialty
                    specialty = appt["type"].split()[0]  # crude extraction e.g. "Cardiologist"
                    doctor = await get_doctor_by_specialty(specialty)

                    if doctor and "slots" in doctor and doctor["slots"]:
                        await assign_slot_to_appointment(patient_id, appt["id"], doctor["doctor_id"])
                        break  # assign one slot for demo

    return careplan


async def get_medication_by_patient(patient_id: str) -> dict:
    doc = await db[CAREPLANS_COLL].find_one({"patient_id": patient_id})
    if not doc:
        return None
    
    # Convert MongoDB ObjectId to string
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)  # remove original ObjectId so JSON is clean

    # Optionally convert created_at to ISO string for JSON
    if "created_at" in doc:
        doc["created_at"] = doc["created_at"].isoformat()
    
    return doc


async def get_careplan() -> dict:
    """
    Fetch the single careplan document in the DB.
    Assumes only one careplan exists.
    """
    doc = await db[CAREPLANS_COLL].find_one({})
    if not doc:
        return None

    # Convert ObjectId to string for clean JSON
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)

    if "created_at" in doc:
        doc["created_at"] = doc["created_at"].isoformat()

    return doc



