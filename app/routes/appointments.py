from fastapi import APIRouter, HTTPException
from app.service.crud_appointments import update_appointment_status, get_careplan_by_appointment_id , get_pending_appointments
from app.utils.ai_agent import assign_slot_to_appointment

router = APIRouter()

@router.post("/appointments/{appointment_id}/confirm")
async def confirm_appointment(appointment_id: str):
    careplan = await update_appointment_status(appointment_id, "confirmed")
    if not careplan:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "ok", "careplan": careplan}

@router.post("/appointments/{appointment_id}/decline")
async def decline_appointment(appointment_id: str):
    careplan = await update_appointment_status(appointment_id, "declined")
    if not careplan:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "ok", "careplan": careplan}

@router.post("/appointments/{appointment_id}/assign-slot")
async def assign_slot_auto(appointment_id: str):
    careplan, appointment = await get_careplan_by_appointment_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    specialty = appointment["type"].split()[0]  # extract specialty

    slot = await assign_slot_to_appointment("1", appointment_id, specialty)  # hardcoded patient_id
    if not slot:
        raise HTTPException(status_code=404, detail="No available slot")

    return {"status": "ok", "proposed_slot": slot}

@router.get("/pending-appointments")
async def pending_appointments():
    pending = await get_pending_appointments()
    return {"pending": pending}
