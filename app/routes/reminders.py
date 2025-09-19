# app/routes/reminders.py
from fastapi import APIRouter, HTTPException, Query
from app.service.crud_reminders import get_reminders, update_reminder_time
from datetime import datetime
import asyncio

router = APIRouter()


@router.get("/")
async def fetch_reminders():
    """
    Fetch reminder slots. Always returns the four slots.
    Each returned slot has a dynamic 'medications' array (built in service).
    """
    reminders = await get_reminders()
    if reminders is None:
        raise HTTPException(status_code=404, detail="No reminders found")
    return {"status": "ok", "reminder_slots": reminders}


@router.post("/{slot}/update-time")
async def update_slot_time(slot: str, time: str = Query(..., description="HH:MM e.g. 08:30")):
    """
    Update the time for the given slot (morning/afternoon/evening/night).
    Use query param: ?time=08:30  (fast for Swagger/curl)
    """
    updated = await update_reminder_time(slot, time)
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update reminder time (missing careplan or slot)")
    return {"status": "ok", "slot": slot, "time": time}


# Background notifier (optional for demo)
async def reminder_notifier():
    """
    Optional helper: run as a background task on startup if you want console notifications.
    Add to main.py startup: asyncio.create_task(reminder_notifier())
    """
    while True:
        slots = await get_reminders()
        now = datetime.now().strftime("%H:%M")
        for slot, data in slots.items():
            if data.get("time") == now and data.get("medications"):
                print(f"[AI Reminder] {slot.capitalize()} meds: {', '.join(data['medications'])}")
        await asyncio.sleep(30)
