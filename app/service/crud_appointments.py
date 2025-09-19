# app/service/crud_appointments.py
from ..database import db
from datetime import datetime

CAREPLAN_COLL = "careplans"
from bson import ObjectId

DOCTOR_AVAIL_COLL = "doctors"  # adjust if your collection name is different

async def update_appointment_status(appointment_id: str, status: str, proposed_slot: str = None):
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan:
        return None

    # update appointment status
    found = False
    for appt in careplan.get("appointments", []):
        if appt["id"] == appointment_id:
            appt["status"] = status
            if proposed_slot:
                appt["proposed_slot"] = proposed_slot
            found = True
            break

    if not found:
        return None

    await db[CAREPLAN_COLL].update_one(
        {"_id": careplan["_id"]},
        {"$set": {"appointments": careplan["appointments"]}}
    )

    # convert _id to str before returning
    careplan["id"] = str(careplan["_id"])
    careplan.pop("_id", None)
    return careplan

async def get_pending_appointments():
    """
    Return all pending appointments from the single careplan in the DB.
    """
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan or "appointments" not in careplan:
        return []

    return [a for a in careplan["appointments"] if a.get("status") == "pending"]

async def get_confirmed_appointments():
    """
    Return all confirmed appointments from the single careplan in the DB.
    """
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan or "appointments" not in careplan:
        return []

    return [a for a in careplan["appointments"] if a.get("status") == "confirmed"]

async def get_careplan_by_appointment_id(appointment_id: str):
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan:
        return None, None

    # convert _id to str
    careplan["id"] = str(careplan["_id"])
    careplan.pop("_id", None)

    appointment = next((a for a in careplan.get("appointments", []) if a["id"] == appointment_id), None)
    return careplan, appointment


async def get_doctor_by_specialty(specialty: str) -> dict:
    doc = await db[DOCTOR_AVAIL_COLL].find_one({"specialty": {"$regex": specialty, "$options": "i"}})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


async def assign_slot_to_appointment(appointment_id: str):
    # 1️⃣ Get careplan + appointment
    careplan, appointment = await get_careplan_by_appointment_id(appointment_id)
    if not appointment:
        return None

    # 2️⃣ Extract specialty from appointment type
    specialty = appointment["type"].split()[0]  # first word

    # 3️⃣ Get doctor by specialty
    doctor = await get_doctor_by_specialty(specialty)
    if not doctor or "available_slots" not in doctor or not doctor["available_slots"]:
        return None

    # 4️⃣ Normalize slots to strings for safe comparison
    def slot_to_str(slot):
        if isinstance(slot, str):
            return slot
        return slot.isoformat()

    booked_slots = [
        slot_to_str(a.get("proposed_slot"))
        for a in careplan.get("appointments", [])
        if a.get("proposed_slot")
    ]

    # 5️⃣ Find first free slot
    proposed_slot = None
    for slot in doctor["available_slots"]:
        if slot_to_str(slot) not in booked_slots:
            proposed_slot = slot
            break

    if not proposed_slot:
        return None

    # 6️⃣ Update appointment in careplan
    for a in careplan["appointments"]:
        if a["id"] == appointment_id:
            a["proposed_slot"] = proposed_slot
            break

    await db[CAREPLAN_COLL].update_one(
        {"_id": ObjectId(careplan["id"])},
        {"$set": {"appointments": careplan["appointments"]}}
    )

    return proposed_slot