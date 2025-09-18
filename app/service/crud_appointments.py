# app/service/crud_appointments.py
from ..database import db
from datetime import datetime

CAREPLAN_COLL = "careplans"
from bson import ObjectId

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
