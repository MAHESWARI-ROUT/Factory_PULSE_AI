from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    referenced_machine_ids: list[str] = []
