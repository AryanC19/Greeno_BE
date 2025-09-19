from fastapi import APIRouter, HTTPException
from app.service import crud_careplan
from app.service.crud_ai_diet_exercise import generate_diet_exercise_plan

router = APIRouter()

@router.get("/", summary="Get Diet & Exercise Plan")
async def get_diet_exercise():
    # Fetch the careplan from the database (async example)
    careplan = await crud_careplan.get_careplan()
    if not careplan:
        raise HTTPException(status_code=404, detail="No careplan found")

    # Extract medical_history from the careplan
    medical_history = careplan.get("medical_history")
    if not medical_history:
        raise HTTPException(status_code=400, detail="No medical history available")

    # Pass medical_history to the AI service
    plan = generate_diet_exercise_plan(medical_history)

    return {"status": "ok", "diet_exercise_plan": plan}
