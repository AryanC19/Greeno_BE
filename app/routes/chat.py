# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from app.service.crud_careplan import get_careplan
from app.service.crud_chat import ask_chatbot
from app.service.instruction_parser import parse_instruction
from app.service.action_dispatcher import dispatch_action
from app.models import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Chat endpoint with lightweight intent execution.
    Flow:
      1. Load careplan (single patient assumption).
      2. Parse instruction via LLM -> structured JSON.
      3. If action recognized (mark_medication) -> dispatch -> build answer.
      4. Else fallback to generic chatbot response.
    Returns only {"answer": ...} to satisfy existing response model.
    """
    try:
        careplan = await get_careplan()
        parsed = parse_instruction(req.question, careplan or {})
        if parsed.get("action") == "mark_medication":
            dispatch_result = await dispatch_action(parsed)
            if dispatch_result.get("success"):
                answer = (
                    f"Marked {parsed.get('medication_name')} as "
                    f"{'taken' if parsed.get('taken') else 'not taken'} for {parsed.get('time')}."  # noqa: E501
                )
            else:
                answer = (
                    "Tried to update medication but failed. "
                    f"(status={dispatch_result.get('status_code') or dispatch_result.get('error')})"
                )
            return {"answer": answer}

        if parsed.get("action") == "update_appointment":
            dispatch_result = await dispatch_action(parsed)
            if dispatch_result.get("success"):
                answer = (
                    f"Appointment '{parsed.get('appointment_label')}' { 'confirmed' if parsed.get('status')=='confirmed' else 'declined' }."
                )
            else:
                answer = (
                    "Tried to update appointment but failed. "
                    f"(status={dispatch_result.get('status_code') or dispatch_result.get('error')})"
                )
            return {"answer": answer}

        # Fallback normal chatbot answer
        answer = await ask_chatbot(req.question)
        return {"answer": answer}
    except Exception as e:
        print(f"[chat_endpoint] Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))