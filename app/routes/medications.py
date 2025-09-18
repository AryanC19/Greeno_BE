
from app.service.crud_medications import toggle_schedule_taken , get_medications
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/api/{medication_id}/schedule/{time}/taken")
async def mark_taken(medication_id: str, time: str):
    return await toggle_schedule_taken(medication_id, time, True)

@router.post("/api/{medication_id}/schedule/{time}/not-taken")
async def mark_not_taken(medication_id: str, time: str):
    return await toggle_schedule_taken(medication_id, time, False)


@router.get("/", summary="Fetch medications")
async def fetch_medications():
    meds = await get_medications()
    if not meds:
        raise HTTPException(status_code=404, detail="No medications found")
    return {"status": "ok", "medications": meds}