from fastapi import APIRouter, HTTPException
from app.service import crud_careplan
from app.service.crud_ai_diet_exercise import (
    generate_diet_exercise_plan,
    generate_only_diet_plan,
    generate_only_exercise_plan,
)

router = APIRouter()

async def _get_med_history() -> str:
    careplan = await crud_careplan.get_careplan()
    if not careplan:
        raise HTTPException(status_code=404, detail="No careplan found")
    medical_history = careplan.get("medical_history")
    if not medical_history:
        raise HTTPException(status_code=400, detail="No medical history available")
    return medical_history

@router.get("/", summary="Get Diet & Exercise Plan (combined)")
async def get_diet_exercise():
    medical_history = await _get_med_history()
    plan = await generate_diet_exercise_plan(medical_history)
    return {"status": "ok", "diet_exercise_plan": plan}

@router.get("/diet", summary="Get Diet Plan Only")
async def get_diet_only():
    medical_history = await _get_med_history()
    diet = await generate_only_diet_plan(medical_history)
    return {"status": "ok", "diet_plan": diet["diet_plan"]}

@router.get("/workouts", summary="Get Exercise Plan Only")
async def get_exercise_only():
    medical_history = await _get_med_history()
    workouts = await generate_only_exercise_plan(medical_history)
    return {"status": "ok", "exercise_plan": workouts["exercise_plan"]}
