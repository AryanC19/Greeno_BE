from ..database import db
from ..utils.ai_agent import get_medicine_reason
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

async def get_medications_with_info() -> dict:
    """
    Fetch medications from database and get AI explanations for why each is prescribed.
    """
    # Fetch the first (and only) careplan
    careplan = await db[CAREPLAN_COLL].find_one()
    if not careplan or "medications" not in careplan:
        return {"medication_info": {}}

    medication_info = {}
    
    # Get unique medication names from the careplan
    for med in careplan["medications"]:
        medicine_name = med.get("name", "")
        if medicine_name and medicine_name not in medication_info:
            try:
                reason = get_medicine_reason(medicine_name)
                medication_info[medicine_name] = reason
            except Exception as e:
                medication_info[medicine_name] = f"Error getting information: {str(e)}"

    return {"medication_info": medication_info}