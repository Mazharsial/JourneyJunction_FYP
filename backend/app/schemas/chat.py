"""Chatbot schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: uuid.UUID | None = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    role: str
    content: str
    meta: dict
    created_at: datetime


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    reply: ChatMessageOut
    intent: str
    status: str  # ok (Gemini) | fallback (grounded)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    messages: list[ChatMessageOut]
