"""
Chatbot evaluation harness.

Measures (1) intent-classification accuracy and (2) visa-grounding accuracy on a
labelled dataset of representative queries. Honest + reproducible: results are
computed, never assumed. Run as a CLI (`python -m app.services.ai.evaluation`)
or via the test suite, which asserts the >= 90% target.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai import grounding
from app.services.ai.grounding import (
    DESTINATION, FLIGHT, GREETING, HOTEL, OUT_OF_SCOPE, PLAN, VISA,
)


@dataclass
class EvalItem:
    query: str
    intent: str
    visa_requirement: str | None = None  # expected grounded fact for visa queries


DATASET: list[EvalItem] = [
    # greetings
    EvalItem("Hi there", GREETING),
    EvalItem("Hello, good morning", GREETING),
    EvalItem("Thanks!", GREETING),
    # visa (with route -> grounding checked)
    EvalItem("Do I need a visa for Dubai from Pakistan?", VISA, "visa required"),
    EvalItem("Is a visa required to travel from the UK to the UAE?", VISA, "visa on arrival"),
    EvalItem("Visa requirements from USA to Dubai", VISA, "visa on arrival"),
    EvalItem("Do Saudi citizens need a visa for the UAE?", VISA, "visa free"),
    EvalItem("What visa do I need for the UAE coming from Turkey?", VISA, "visa on arrival"),
    EvalItem("Passport requirement for France to Dubai", VISA, "visa on arrival"),
    EvalItem("visa for dubai from pakistan", VISA, "visa required"),
    EvalItem("Do I need a visa?", VISA),
    # flights
    EvalItem("Find me flights from Lahore to Dubai", FLIGHT),
    EvalItem("What's the cheapest flight to Dubai?", FLIGHT),
    EvalItem("Show airfare from Karachi to Dubai", FLIGHT),
    EvalItem("I want to fly to Istanbul", FLIGHT),
    # hotels
    EvalItem("Suggest hotels in Dubai", HOTEL),
    EvalItem("I need accommodation in Abu Dhabi", HOTEL),
    EvalItem("Where can I stay in Dubai on a budget?", HOTEL),
    EvalItem("Book me a resort in Dubai", HOTEL),
    # plan
    EvalItem("Help me plan a trip to Dubai", PLAN),
    EvalItem("Create an itinerary for 5 days in Dubai", PLAN),
    EvalItem("Plan my trip from Lahore to Dubai", PLAN),
    # destination
    EvalItem("What's the best time to visit Dubai?", DESTINATION),
    EvalItem("Things to do in Dubai", DESTINATION),
    EvalItem("Tell me about Istanbul", DESTINATION),
    # out of scope
    EvalItem("What is 2 + 2?", OUT_OF_SCOPE),
    EvalItem("Write me a Python function", OUT_OF_SCOPE),
    EvalItem("Who won the football match yesterday?", OUT_OF_SCOPE),
]


def evaluate_intents() -> dict:
    total = len(DATASET)
    failures = []
    for item in DATASET:
        predicted = grounding.detect_intent(item.query)
        if predicted != item.intent:
            failures.append({"query": item.query, "expected": item.intent, "got": predicted})
    correct = total - len(failures)
    return {"total": total, "correct": correct, "accuracy": correct / total, "failures": failures}


async def evaluate_grounding(session: AsyncSession) -> dict:
    items = [i for i in DATASET if i.visa_requirement]
    failures = []
    for item in items:
        ctx = await grounding.build_context(session, item.query)
        facts_text = " ".join(ctx["facts"]).lower()
        if item.visa_requirement.lower() not in facts_text:
            failures.append({"query": item.query, "expected": item.visa_requirement, "facts": ctx["facts"]})
    total = len(items)
    correct = total - len(failures)
    return {"total": total, "correct": correct, "accuracy": correct / total, "failures": failures}


def _main() -> None:
    import asyncio

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    from app.db.seed_locations import seed_locations
    from app.models import Base

    async def run():
        intent = evaluate_intents()
        engine = create_async_engine("sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        async with engine.begin() as c:
            await c.run_sync(Base.metadata.create_all)
        sm = async_sessionmaker(engine, expire_on_commit=False)
        async with sm() as s:
            await seed_locations(s)
            await s.commit()
            ground = await evaluate_grounding(s)
        await engine.dispose()

        print("=== Journey Junction Chatbot Evaluation ===")
        print(f"Intent classification: {intent['correct']}/{intent['total']} = {intent['accuracy']:.1%}")
        for f in intent["failures"]:
            print(f"  MISS: {f}")
        print(f"Visa grounding:        {ground['correct']}/{ground['total']} = {ground['accuracy']:.1%}")
        for f in ground["failures"]:
            print(f"  MISS: {f}")

    asyncio.run(run())


if __name__ == "__main__":
    _main()
