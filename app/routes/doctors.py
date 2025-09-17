from fastapi import APIRouter, HTTPException
from app.utils.ai_agent import assign_slot_to_appointment
from ..models import DoctorAvailability
from ..service.crud_doctor_availabilty import create_doctor_availability, get_doctor_availability_by_id

router = APIRouter()

# 1. Add a doctor availability
@router.post("/doctor-availability")
async def add_doctor_availability(doc: DoctorAvailability):
    inserted = await create_doctor_availability(doc.dict())
    return {"status": "ok", "doctor": inserted}

# 2. Get doctor availability by doctor_id
@router.get("/doctor-availability/{doctor_id}")
async def get_doctor_availability(doctor_id: str):
    doc = await get_doctor_availability_by_id(doctor_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doc
