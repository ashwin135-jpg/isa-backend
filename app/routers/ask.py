import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/ask", tags=["AI"])

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # set this in Render Env Vars
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class AskRequest(BaseModel):
    question: str


@router.post("/")
def ask(req: AskRequest):
    q = (req.question or "").strip()
    if not q:
        return {"answer": "Ask a question about aerospace engineering."}

    if not GROQ_API_KEY:
        # This is the #1 reason you keep seeing the placeholder behavior
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set on the server.")

    payload = {
        # Pick a Groq model. This is a safe default:
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are ISA Master Tool AI, a helpful aerospace engineering tutor. "
                    "Be concise, correct, and show equations when useful."
                ),
            },
            {"role": "user", "content": q},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }

    try:
        r = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        answer = data["choices"][0]["message"]["content"].strip()
        return {"answer": answer}
    except requests.HTTPError:
        # show Groq error details (very useful)
        raise HTTPException(status_code=500, detail=f"Groq error: {r.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
