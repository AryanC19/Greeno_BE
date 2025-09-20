# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
from app.service.crud_careplan import get_careplan
from app.service.crud_chat import ask_chatbot
from app.models import ChatRequest, ChatResponse
router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        answer = await ask_chatbot(req.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))