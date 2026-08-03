from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_assistant import ChatAssistantService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
def ask(
    payload: ChatRequest,
    service: ChatAssistantService = Depends(get_chat_service),
) -> ChatResponse:
    answer, referenced_ids = service.ask(payload.question)
    return ChatResponse(answer=answer, referenced_machine_ids=referenced_ids)
