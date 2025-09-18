from ..database import db
import uuid
from bson import ObjectId


CAREPLAN_COLL = "careplans"
async def toggle_schedule_taken(medication_id: str, time: str, value: bool):
    result = await db.careplans.update_one(
        {"medications.id": medication_id, "medications.schedule.time": time},
        {"$set": {"medications.$[m].schedule.$[s].taken": value}},
        array_filters=[
            {"m.id": medication_id},
            {"s.time": time}
        ]
    )
    return {"updated": result.modified_count}



async def get_medications() -> dict:
    # fetch the first (and only) careplan
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan or "medications" not in careplan:
        return {"morning": [], "afternoon": [], "evening": [], "night": []}

    meds = {"morning": [], "afternoon": [], "evening": [], "night": []}

    for med in careplan["medications"]:
        for sched in med.get("schedule", []):  # same as reminders
            time = sched.get("time")
            taken = sched.get("taken", False)
            if time in meds:
                meds[time].append({
                    "id": med.get("id", str(uuid.uuid4())),
                    "medication": med.get("name", ""),
                    "dose": med.get("dose", ""),
                    "taken": taken
                })

    return meds