from app.utils.ai_agent import (
    parse_sections,
    extract_entities,
    generate_suggestions
)
import asyncio

# Original synchronous logic extracted into a private helper so we can run it in a thread pool

def _generate_diet_exercise_plan_sync(medical_history: str) -> dict:
    sections = parse_sections(medical_history)
    extraction = extract_entities(
        medical_history,
        sections.get('lab_reports', ''),
        sections.get('allergies', '')
    )
    suggestions = generate_suggestions(
        extraction.get('conditions', []),
        extraction.get('concern', ''),
        sections.get('current_diet', ''),
        extraction.get('lab_metrics', []),
        extraction.get('allergies', [])
    )
    return {
        "status": "success",
        "diet_plan": suggestions.get('diet_plan', ["Try to include the following foods to improve your diet"]),
        "exercise_plan": suggestions.get('exercise_plan', ["None"]),
        # keep raw sections if needed for debugging in separated endpoints
        "_sections": sections,
        "_extraction": extraction
    }

# New async wrapper to avoid blocking the event loop with heavy synchronous network I/O
async def generate_diet_exercise_plan(medical_history: str) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _generate_diet_exercise_plan_sync(medical_history))

# New separated convenience helpers
async def generate_only_diet_plan(medical_history: str) -> dict:
    data = await generate_diet_exercise_plan(medical_history)
    return {"status": data["status"], "diet_plan": data["diet_plan"]}

async def generate_only_exercise_plan(medical_history: str) -> dict:
    data = await generate_diet_exercise_plan(medical_history)
    return {"status": data["status"], "exercise_plan": data["exercise_plan"]}