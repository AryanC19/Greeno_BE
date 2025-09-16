# app/crud.py
import uuid
from datetime import datetime
from ..database import db

CAREPLANS_COLL = "careplans"

async def create_careplan(careplan: dict) -> dict:
    # Ensure each med and appointment has an id & default status
    for med in careplan.get("medications", []):
        med.setdefault("id", str(uuid.uuid4()))
    for appt in careplan.get("appointments", []):
        appt.setdefault("id", str(uuid.uuid4()))
        appt.setdefault("status", "pending")
    careplan_doc = {
        "patient_id": careplan["patient_id"],
        "medications": careplan.get("medications", []),
        "appointments": careplan.get("appointments", []),
        "created_at": datetime.utcnow()
    }
    res = await db[CAREPLANS_COLL].insert_one(careplan_doc)
    careplan_doc["_id"] = str(res.inserted_id)
    return careplan_doc

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


async def get_pending_appointments(patient_id: str) -> list:
    doc = await get_medication_by_patient(patient_id)
    if not doc:
        return []
    return [a for a in doc.get("appointments", []) if a.get("status") == "pending"]

async def update_appointment_status(patient_id: str, appointment_id: str, status: str, proposed_slot: str = None) -> dict:
    query = {"patient_id": patient_id, "appointments.id": appointment_id}
    update_fields = {"appointments.$.status": status}
    if proposed_slot is not None:
        update_fields["appointments.$.proposed_slot"] = proposed_slot
    await db[CAREPLANS_COLL].update_one(query, {"$set": update_fields})
    return await get_medication_by_patient(patient_id)
