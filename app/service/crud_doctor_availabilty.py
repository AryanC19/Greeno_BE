# app/crud.py
import uuid
from datetime import datetime
from ..database import db

DOCTOR_AVAIL_COLL = "doctor_availability"

async def create_doctor_availability(doc: dict) -> dict:
    res = await db[DOCTOR_AVAIL_COLL].insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc

async def get_doctor_availability_by_id(doctor_id: str) -> dict:
    doc = await db[DOCTOR_AVAIL_COLL].find_one({"doctor_id": doctor_id})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc
async def get_doctor_by_specialty(specialty: str) -> dict:
    doc = await db[DOCTOR_AVAIL_COLL].find_one({"specialty": {"$regex": specialty, "$options": "i"}})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc