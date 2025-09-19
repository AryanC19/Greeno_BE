
from app.service.crud_medications import toggle_schedule_taken , get_medications, get_medications_with_info
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

@router.get("/info", summary="Get medication information")
async def get_medication_info():
    """
    Fetch medications from database and get AI explanations for why each is prescribed.
    """
    try:
        result = await get_medications_with_info()
        return {"status": "ok", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting medication info: {str(e)}")