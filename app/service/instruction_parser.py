import os
import json
from typing import Any, Dict, List
from openai import OpenAI

# Reuse existing OpenRouter setup – using same env var as crud_chat
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY_CHATBOT")
)

ALLOWED_TIMES = ["morning", "afternoon", "evening", "night"]

def _build_appointment_index(careplan: dict) -> Dict[str, Dict[str, Any]]:
    """Case-insensitive map from an appointment label to its object.
    Uses 'type' if present, otherwise falls back to id.
    """
    appts: Dict[str, Dict[str, Any]] = {}
    for appt in (careplan or {}).get("appointments", []):
        label = (appt.get("type") or appt.get("id") or "").strip()
        if label:
            appts[label.lower()] = appt
    return appts


def _build_medication_index(careplan: dict) -> Dict[str, Dict[str, Any]]:
    """Case-insensitive map from medication name to its object."""
    meds: Dict[str, Dict[str, Any]] = {}
    for med in (careplan or {}).get("medications", []):
        name = (med.get("name") or "").strip()
        if name:
            meds[name.lower()] = med
    return meds


def parse_instruction(question: str, careplan: dict) -> Dict[str, Any]:
    """Parse a user instruction into a normalized JSON action.
    Supported (hackathon scope):
      - mark_medication
      - update_appointment (confirm/decline)
    Returns {"action": "none"} if unrecognized.
    """
    medication_index = _build_medication_index(careplan)
    medication_names: List[str] = list(medication_index.keys())
    appointment_index = _build_appointment_index(careplan)
    appointment_labels: List[str] = list(appointment_index.keys())

    system_prompt = (
        'You are an intent-to-JSON parser for a healthcare careplan assistant. '
        'You MUST output ONLY valid JSON (no code fences, no explanation). '
        'Supported intents:\n'
        '1) Mark a medication as taken/not taken. Output: {"action":"mark_medication","medication_name":"<exact name from list>","time":"<morning|afternoon|evening|night>","taken":true|false}\n'
        '2) Confirm or decline an appointment. Output: {"action":"update_appointment","appointment_label":"<exact label from list>","status":"confirmed|declined"}\n'
        'Medication times allowed: morning, afternoon, evening, night (ONLY these).\n'
        'Rules:\n'
        "- For appointments: interpret verbs like 'confirm', 'accept' => confirmed; 'decline', 'cancel', 'reject' => declined.\n"
        '- Use only labels from provided list; if no match, return {"action":"none"}.\n'
        '- Do NOT hallucinate names.\n'
        '- Output exactly one JSON object.'
    )

    user_prompt = (
        f"Medication names: {medication_names}\n"
        f"Appointment labels: {appointment_labels}\n"
        f"User query: {question}\n"
        "Return JSON now."
    )

    try:
        resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,
            temperature=0
        )
        raw = resp.choices[0].message.content.strip()
        first_brace = raw.find("{")
        last_brace = raw.rfind("}")
        if first_brace == -1 or last_brace == -1:
            print(f"[instruction_parser] No JSON braces found in model output: {raw}")
            return {"action": "none", "reason": "no_json"}
        raw_json = raw[first_brace:last_brace + 1]
        parsed = json.loads(raw_json)
    except Exception as e:
        print(f"[instruction_parser] LLM parse error: {e}")
        return {"action": "none", "reason": "parse_error"}

    action_type = parsed.get("action")

    # Medication path
    if action_type == "mark_medication":
        med_name = (parsed.get("medication_name") or "").lower().strip()
        time_slot = (parsed.get("time") or "").lower().strip()
        taken = parsed.get("taken")

        if med_name not in medication_index:
            return {"action": "none", "reason": "medication_not_found", "medication_name": med_name}
        if time_slot not in ALLOWED_TIMES:
            return {"action": "none", "reason": "invalid_time", "time": time_slot}
        if not isinstance(taken, bool):
            return {"action": "none", "reason": "invalid_taken_flag"}

        med_obj = medication_index[med_name]
        medication_id = med_obj.get("id") or med_obj.get("_id")
        if not medication_id:
            return {"action": "none", "reason": "medication_missing_id"}

        result = {
            "action": "mark_medication",
            "medication_id": medication_id,
            "medication_name": med_obj.get("name"),
            "time": time_slot,
            "taken": taken
        }
        print(f"[instruction_parser] Parsed action: {result}")
        return result

    # Appointment path
    if action_type == "update_appointment":
        label = (parsed.get("appointment_label") or "").lower().strip()
        status = (parsed.get("status") or "").lower().strip()
        if label not in appointment_index:
            return {"action": "none", "reason": "appointment_not_found", "appointment_label": label}
        if status not in ("confirmed", "declined"):
            return {"action": "none", "reason": "invalid_status", "status": status}
        appt_obj = appointment_index[label]
        appt_id = appt_obj.get("id") or appt_obj.get("_id")
        if not appt_id:
            return {"action": "none", "reason": "appointment_missing_id"}
        result = {
            "action": "update_appointment",
            "appointment_id": appt_id,
            "appointment_label": appt_obj.get("type") or label,
            "status": status
        }
        print(f"[instruction_parser] Parsed action: {result}")
        return result

    return {"action": "none"}
