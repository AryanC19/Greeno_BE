import os
from typing import Dict, Any
import httpx

# Internal base URL (same service or gateway). Override via env if needed.
BASE_INTERNAL_URL = os.getenv("INTERNAL_API_BASE", "http://localhost:8000")

async def dispatch_action(action: Dict[str, Any]) -> Dict[str, Any]:
    """Execute parsed action by calling existing endpoints.
    Supports:
      - mark_medication
      - update_appointment (confirm / decline)
    Returns structured result for debugging.
    """
    act = action.get("action")

    if act == "mark_medication":
        medication_id = action["medication_id"]
        time_slot = action["time"]
        taken = action["taken"]
        endpoint = f"/api/medications/api/{medication_id}/schedule/{time_slot}/" + ("taken" if taken else "not-taken")
    elif act == "update_appointment":
        appointment_id = action["appointment_id"]
        status = action["status"]  # confirmed | declined
        endpoint = f"/api/appointments/{appointment_id}/" + ("confirm" if status == "confirmed" else "decline")
    else:
        return {"success": False, "error": "unsupported_action"}

    url = BASE_INTERNAL_URL.rstrip("/") + endpoint
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url)
        data = {
            "success": 200 <= resp.status_code < 300,
            "status_code": resp.status_code,
            "endpoint": endpoint,
        }
        if not data["success"]:
            data["body"] = resp.text[:500]
        print(f"[action_dispatcher] Dispatch result: {data}")
        return data
    except Exception as e:
        err = {"success": False, "error": str(e), "endpoint": endpoint}
        print(f"[action_dispatcher] Exception: {err}")
        return err
