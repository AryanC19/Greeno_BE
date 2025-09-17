from fastapi import APIRouter, HTTPException
from app.service.crud_careplan import update_appointment_status
from app.utils.ai_agent import assign_slot_to_appointment
from ..models import DoctorAvailability
from ..service.crud_doctor_availabilty import create_doctor_availability, get_doctor_availability_by_id

router = APIRouter()

# Confirm appointment (status = confirmed)
@router.post("/appointments/{appointment_id}/confirm")
async def confirm_appointment(patient_id: str, appointment_id: str):
    careplan = await update_appointment_status(patient_id, appointment_id, "confirmed")
    if not careplan:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "ok", "careplan": careplan}

# Decline appointment (status = declined)
@router.post("/appointments/{appointment_id}/decline")
async def decline_appointment(patient_id: str, appointment_id: str):
    careplan = await update_appointment_status(patient_id, appointment_id, "declined")
    if not careplan:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"status": "ok", "careplan": careplan}



@router.post("/appointments/{appointment_id}/assign-slot")
async def assign_slot_auto(appointment_id: str):
    """
    Automatically finds a matching doctor by specialty and assigns the first available slot.
    """
    from ..service.crud_careplan import get_careplan_by_appointment_id
    from ..utils.ai_agent import assign_slot_to_appointment

    # 1. Get patient ID from appointment
    careplan, appointment = await get_careplan_by_appointment_id(appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient_id = careplan["patient_id"]
    specialty = appointment["type"].split()[0]  # extract specialty

    # 2. Assign slot automatically
    slot = await assign_slot_to_appointment(patient_id, appointment_id, specialty)
    if not slot:
        raise HTTPException(status_code=404, detail="No available slot")

    return {"status": "ok", "proposed_slot": slot}
