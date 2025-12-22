from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ask", tags=["AI"])

class AskRequest(BaseModel):
    question: str

@router.post("")
def ask(req: AskRequest):
    q = (req.question or "").strip()
    if not q:
        return {"answer": "Ask a question about aerospace engineering."}

    # Placeholder (no real AI wired yet)
    return {"answer": f"AI endpoint is live. You asked: {q}"}
