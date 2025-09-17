from fastapi import APIRouter, HTTPException

from app.service.crud_reminders import get_reminders

router = APIRouter()

@router.get("/reminders")
async def fetch_reminders():
    reminders = await get_reminders()
    if not reminders:
        raise HTTPException(status_code=404, detail="No medications found")
    return {"status": "ok", "reminders": reminders}
