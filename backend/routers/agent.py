from fastapi import APIRouter
from pydantic import BaseModel
from backend.services.extraction import agent_chat, search_drawings

router = APIRouter(prefix="/api", tags=["agent"])


class ChatRequest(BaseModel):
    question: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.post("/agent/chat")
def chat(req: ChatRequest):
    """Chat with the drawing analysis agent."""
    answer = agent_chat(req.question)
    return {"answer": answer, "question": req.question}


@router.post("/agent/search")
def search(req: SearchRequest):
    """Direct search against Cortex Search."""
    results = search_drawings(req.query, req.limit)
    return {"results": results, "query": req.query}
