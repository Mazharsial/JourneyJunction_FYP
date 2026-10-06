"""
Subscription plans and feature entitlements (single source of truth).

Entitlements are seeded into the DB (plans + plan_features) and enforced
server-side. `limit_value`: -1 = unlimited, 0 = disabled, N = monthly cap.
Flags use `enabled` (limit ignored).
"""
from __future__ import annotations


class Plans:
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"


class Features:
    TRIP_PLANNING = "trip_planning"      # flag
    CHATBOT_MESSAGES = "chatbot_messages"  # monthly limit
    OCR_DOCUMENTS = "ocr_documents"        # monthly limit
    WHATSAPP = "whatsapp"                # flag
    PRIORITY_SUPPORT = "priority_support"  # flag


# plan code -> spec
PLAN_SPECS = {
    Plans.FREE: {
        "name": "Free", "price_cents": 0, "sort_order": 0,
        "description": "Get started with core trip planning and a taste of AI.",
        "features": {
            Features.TRIP_PLANNING: (True, -1),
            Features.CHATBOT_MESSAGES: (True, 20),
            Features.OCR_DOCUMENTS: (True, 3),
            Features.WHATSAPP: (False, 0),
            Features.PRIORITY_SUPPORT: (False, 0),
        },
    },
    Plans.PRO: {
        "name": "Pro", "price_cents": 999, "sort_order": 1,
        "description": "For frequent travellers — more AI, more document checks.",
        "features": {
            Features.TRIP_PLANNING: (True, -1),
            Features.CHATBOT_MESSAGES: (True, 500),
            Features.OCR_DOCUMENTS: (True, 50),
            Features.WHATSAPP: (False, 0),
            Features.PRIORITY_SUPPORT: (True, -1),
        },
    },
    Plans.BUSINESS: {
        "name": "Business", "price_cents": 2999, "sort_order": 2,
        "description": "Highest limits, WhatsApp assistant and priority support.",
        "features": {
            Features.TRIP_PLANNING: (True, -1),
            Features.CHATBOT_MESSAGES: (True, 5000),
            Features.OCR_DOCUMENTS: (True, 500),
            Features.WHATSAPP: (True, -1),
            Features.PRIORITY_SUPPORT: (True, -1),
        },
    },
}

PAID_PLANS = [Plans.PRO, Plans.BUSINESS]
DEFAULT_PLAN = Plans.FREE
