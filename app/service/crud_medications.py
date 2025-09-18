from ..database import db

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

