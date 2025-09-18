import uuid
from ..database import db

CAREPLAN_COLL = "careplans"

async def get_reminders() -> dict:
    # fetch the first (and only) careplan
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan or "medications" not in careplan:
        return {"morning": [], "afternoon": [], "evening": [], "night": []}

    reminders = {"morning": [], "afternoon": [], "evening": [], "night": []}

    for med in careplan["medications"]:
        for sched in med.get("schedule", []):  # <-- changed from timing
            time = sched.get("time")
            taken = sched.get("taken", False)
            if time in reminders:
                reminders[time].append({
                    "id": med.get("id", str(uuid.uuid4())),
                    "medication": med.get("name", ""),
                    "dose": med.get("dose", ""),
                    "taken": taken   # include per-time taken status
                })

    return reminders
