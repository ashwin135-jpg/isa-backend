from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ask", tags=["AI"])

class AskRequest(BaseModel):
    question: str

@router.post("")
def ask(req: AskRequest):
    q = (req.question or "").strip()
    if not q:
        return {"answer": "Ask me a question about aerospace engineering."}

    # Placeholder response (no LLM wired yet)
    return {
        "answer": (
            "AI is not fully enabled yet. "
            "But I received your question: "
            f"“{q}”. "
            "Coming soon: real aerospace Q&A."
        )
    }
