
from app.service.crud_medications import toggle_schedule_taken
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/api/{medication_id}/schedule/{time}/taken")
async def mark_taken(medication_id: str, time: str):
    return await toggle_schedule_taken(medication_id, time, True)

@router.post("/api/{medication_id}/schedule/{time}/not-taken")
async def mark_not_taken(medication_id: str, time: str):
    return await toggle_schedule_taken(medication_id, time, False)

