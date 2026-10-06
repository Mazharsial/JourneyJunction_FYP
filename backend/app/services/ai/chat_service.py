"""AI chat orchestration: grounding -> Gemini (or grounded fallback) -> persist."""
from __future__ import annotations

import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.entitlements import Features
from app.core.logging import get_logger
from app.models.chat import AIRequest, ChatConversation, ChatMessage
from app.services.ai import gemini_client, grounding
from app.services.billing import entitlement_service

logger = get_logger("chat")

_PERSONA = (
    "You are Journey Junction's travel assistant. You help travellers with destinations, "
    "flights, hotels, itineraries and visa guidance. The initial market is Dubai (UAE) "
    "but you support other locations.\n"
    "Rules:\n"
    "- Use ONLY the verified facts provided below for visa/requirement questions. If a fact "
    "is not provided, say you don't have verified information and advise checking the official "
    "government source — do NOT invent visa rules, prices or dates.\n"
    "- For any visa answer, add a short disclaimer that it is informational only.\n"
    "- When the user asks about visa requirements or visa types, list the available visa options "
    "from the verified facts with their duration, fee and key conditions, and mention required "
    "documents and any mandatory health/vaccination steps when provided.\n"
    "- Be concise, friendly and practical. Stay on travel topics.\n"
    "- If the question is not about travel, politely steer back to travel."
)


def _system_instruction(ctx: dict) -> str:
    facts = ctx.get("facts") or []
    market = ctx.get("market") or {}
    block = "\n".join(f"- {f}" for f in facts) if facts else "- (no specific verified facts for this query)"
    market_line = (
        f"Default market: {market.get('city')}, {market.get('country')} "
        f"(currency {market.get('currency')})." if market else ""
    )
    return f"{_PERSONA}\n\n{market_line}\n\nVerified facts:\n{block}"


async def _get_or_create_conversation(
    session: AsyncSession, user_id: uuid.UUID, conversation_id: uuid.UUID | None
) -> ChatConversation | None:
    if conversation_id:
        convo = await session.scalar(
            select(ChatConversation).where(
                ChatConversation.id == conversation_id,
                ChatConversation.user_id == user_id,
            )
        )
        return convo  # None if not owned/found
    convo = ChatConversation(user_id=user_id, title="New conversation", messages=[])
    session.add(convo)
    await session.flush()
    return convo


async def send_message(
    session: AsyncSession, user_id: uuid.UUID, message: str,
    conversation_id: uuid.UUID | None = None,
):
    convo = await _get_or_create_conversation(session, user_id, conversation_id)
    if convo is None:
        return None, None, None  # route -> 404

    # Server-side entitlement enforcement (monthly AI message limit by plan).
    await entitlement_service.consume(session, user_id, Features.CHATBOT_MESSAGES)

    ctx = await grounding.build_context(session, message)
    history = [{"role": m.role, "content": m.content} for m in convo.messages][-get_settings().ai_max_history:]
    system_instruction = _system_instruction(ctx)

    settings = get_settings()
    started = time.monotonic()
    status = "fallback"
    answer = ""
    if gemini_client.is_configured():
        try:
            answer = await gemini_client.generate(
                system_instruction=system_instruction, history=history, user_message=message,
            )
            status = "ok"
        except gemini_client.GeminiError as exc:
            logger.warning("gemini_fallback", error=str(exc))
            answer = grounding.grounded_fallback(message, ctx)
    else:
        answer = grounding.grounded_fallback(message, ctx)
    latency_ms = int((time.monotonic() - started) * 1000)

    # Persist conversation turn.
    convo.messages.append(ChatMessage(role="user", content=message, meta={"intent": ctx["intent"]}))
    assistant_msg = ChatMessage(
        role="assistant", content=answer,
        meta={"intent": ctx["intent"], "status": status, "provider": "gemini" if status == "ok" else "grounded"},
    )
    convo.messages.append(assistant_msg)
    if convo.title == "New conversation":
        convo.title = (message[:60] + "…") if len(message) > 60 else message

    session.add(AIRequest(
        user_id=user_id, kind="chat",
        provider="gemini" if status == "ok" else "grounded",
        model=settings.gemini_model if status == "ok" else "",
        status=status, latency_ms=latency_ms,
        prompt_chars=len(message) + len(system_instruction), response_chars=len(answer),
    ))
    await session.flush()
    return convo, assistant_msg, {
        "intent": ctx["intent"], "status": status,
        "sources": ctx.get("sources", []), "suggestions": ctx.get("suggestions", []),
    }


async def list_conversations(session: AsyncSession, user_id: uuid.UUID) -> list[ChatConversation]:
    return list(
        (await session.scalars(
            select(ChatConversation).where(ChatConversation.user_id == user_id)
            .order_by(ChatConversation.updated_at.desc())
        )).all()
    )


async def get_conversation(
    session: AsyncSession, user_id: uuid.UUID, conversation_id: uuid.UUID
) -> ChatConversation | None:
    return await session.scalar(
        select(ChatConversation).where(
            ChatConversation.id == conversation_id, ChatConversation.user_id == user_id
        )
    )
