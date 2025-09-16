import uuid
from datetime import datetime
from ..database import db

CAREPLAN_COLL = "careplans"

async def get_reminders(patient_id: str) -> dict:
    careplan = await db[CAREPLAN_COLL].find_one({"patient_id": patient_id})
    if not careplan or "medications" not in careplan:
        return {"morning": [], "afternoon": [], "evening": []}

    reminders = {"morning": [], "afternoon": [], "evening": []}

    for med in careplan["medications"]:
        for time in med.get("timing", []):
            if time in reminders:
                reminders[time].append({
                    "id": str(uuid.uuid4()),
                    "medication": med["name"],
                    "dose": med["dose"]
                })

    return reminders
