"""AI travel assistant endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permissions
from app.core.exceptions import AppError
from app.core.rate_limit import RateLimiter
from app.core.rbac import Perms
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import (
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    ConversationDetail,
    ConversationOut,
)
from app.services.ai import chat_service

router = APIRouter()
# Protect the (potentially paid) AI endpoint from abuse.
_chat_limit = RateLimiter(max_requests=20, window_seconds=60, scope="chat")


@router.post("/", response_model=ChatResponse, dependencies=[Depends(_chat_limit)])
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.CHATBOT_USE)),
):
    convo, reply, meta = await chat_service.send_message(
        db, user.id, payload.message, payload.conversation_id
    )
    if convo is None:
        raise AppError("Conversation not found.", code="conversation_not_found", status_code=404)
    return ChatResponse(
        conversation_id=convo.id,
        reply=ChatMessageOut.model_validate(reply),
        intent=meta["intent"],
        status=meta["status"],
    )


@router.get("/conversations", response_model=list[ConversationOut])
async def conversations(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.CHATBOT_USE)),
):
    return await chat_service.list_conversations(db, user.id)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def conversation_detail(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permissions(Perms.CHATBOT_USE)),
):
    convo = await chat_service.get_conversation(db, user.id, conversation_id)
    if not convo:
        raise AppError("Conversation not found.", code="conversation_not_found", status_code=404)
    return convo
