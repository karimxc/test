from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.ai.assistant import AIAssistant
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


class AIQueryRequest(BaseModel):
    question: str


class AIQueryResponse(BaseModel):
    question: str
    answer: str


@router.post("/query", response_model=AIQueryResponse)
def query_assistant(data: AIQueryRequest, db: Session = Depends(get_db)):
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI assistant is not configured. Please set OPENAI_API_KEY.",
        )
    try:
        assistant = AIAssistant(db)
        answer = assistant.query(data.question)
        return AIQueryResponse(question=data.question, answer=answer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI query failed: {str(e)}",
        )
