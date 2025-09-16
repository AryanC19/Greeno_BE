from fastapi import APIRouter, HTTPException

from app.service.crud_reminders import get_reminders

router = APIRouter()

# Get reminders for a patient
@router.get("/patients/{patient_id}/reminders")
async def fetch_reminders(patient_id: str):
    reminders = await get_reminders(patient_id)
    if reminders is None:
        raise HTTPException(status_code=404, detail="Patient not found or no medications")
    return {"status": "ok", "reminders": reminders}
