# app/service/crud_reminders.py
from ..database import db
from typing import Dict

CAREPLAN_COLL = "careplans"


def _default_slots():
    return {
        "morning": {"time": None},
        "afternoon": {"time": None},
        "evening": {"time": None},
        "night": {"time": None},
    }


async def get_reminders() -> Dict[str, dict]:
    """
    Return reminder_slots for the single careplan.
    - If no careplan exists, return default empty slots.
    - Do NOT create new DB documents.
    - Attach medication names to each slot dynamically (not persisted).
    """
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan:
        return _default_slots()

    reminder_slots = careplan.get("reminder_slots", _default_slots())

    # Ensure all four slots exist (defensive)
    for s, v in _default_slots().items():
        if s not in reminder_slots:
            reminder_slots[s] = v

    # Build meds-per-slot dynamically (do NOT write back to DB)
    meds = careplan.get("medications", [])
    # initialize meds lists in the returned structure (temporary, not saved)
    for slot in reminder_slots:
        reminder_slots[slot]["medications"] = []

    for m in meds:
        name = m.get("name")
        for sched in m.get("schedule", []):
            slot = sched.get("time")
            if slot and slot in reminder_slots and name not in reminder_slots[slot]["medications"]:
                reminder_slots[slot]["medications"].append(name)

    return reminder_slots


async def update_reminder_time(slot: str, time: str):
    """
    Update the reminder_slots.<slot>.time inside the single careplan doc.
    - Returns the updated reminder_slots dict on success, or None if careplan/slot missing.
    """
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan:
        return None

    reminder_slots = careplan.get("reminder_slots", _default_slots())

    if slot not in reminder_slots:
        # defensive: if slot key missing, don't create new careplan doc; return None
        return None

    reminder_slots[slot]["time"] = time

    await db[CAREPLAN_COLL].update_one(
        {"_id": careplan["_id"]},
        {"$set": {"reminder_slots": reminder_slots}}
    )

    # Return reminder_slots (fresh view)
    return reminder_slots
