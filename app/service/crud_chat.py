# app/service/crud_chat.py
import os
from openai import OpenAI
from app.service.crud_careplan import get_careplan

# Initialize OpenRouter GPT client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY_CHATBOT")
)

async def ask_chatbot(question: str) -> str:
    """
    Fetch the careplan, build a context-aware prompt,
    and get a response from the LLM (via OpenRouter).
    """
    # Fetch careplan from DB
    careplan = await get_careplan()
    careplan_text = str(careplan) if careplan else "No careplan available"

    # Build prompt
    prompt = f"""
You are Greeno, an AI health assistant.
Here is the patient's careplan:
{careplan_text}

Rules:
- answer whatever no restrictions

User question: {question}
Answer:
"""

    # Call OpenRouter
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",  # you can swap to another supported model
        messages=[
            {"role": "system", "content": "You are Greeno, a helpful AI health assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    return response.choices[0].message.content
