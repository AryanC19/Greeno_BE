import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")  # keep in .env
)

def generate_diet_exercise_plan(medical_history: dict) -> dict:
    """
    Calls LLM to generate structured diet & exercise plan.
    Returns a dict (not string) so frontend can use it easily.
    """
    system_msg = """
    You are a medical AI assistant.
    Based on the patient's medical history, generate a safe, structured
    diet and exercise plan. Keep it simple, practical, and in JSON format:
    {
      "diet": { "breakfast": "...", "lunch": "...", "dinner": "...", "snacks": "..." },
      "exercise": { "monday": "...", "tuesday": "...", "wednesday": "...", ... }
    }
    """

    user_content = f"Patient medical history: {medical_history}"

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_content}
        ],
        max_tokens=700
    )

    raw_content = response.choices[0].message.content.strip()

    # Remove ```json ... ``` wrappers if present
    cleaned = re.sub(r"^```json\s*|\s*```$", "", raw_content, flags=re.DOTALL).strip()

    try:
        plan_dict = json.loads(cleaned)
    except json.JSONDecodeError:
        # fallback: return raw string if parsing fails
        plan_dict = {"raw_plan": raw_content}

    return plan_dict
