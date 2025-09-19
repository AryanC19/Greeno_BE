from app.utils.ai_agent import (
    parse_sections,
    extract_entities,
    generate_suggestions
)

def generate_diet_exercise_plan(medical_history: str) -> dict:
    # Orchestrate the AI logic using the medical_history string
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
        "nutrition_plan": suggestions.get('nutrition_plan', ["Try to include the following foods to improve your nutrition"]),
        "exercise_plan": suggestions.get('exercise_plan', ["None"])
    }