"""
ORM models package.

Importing the model modules here ensures Alembic autogenerate and
`Base.metadata` discover every table.
"""
from app.db.base import Base  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.auth import (  # noqa: F401
    EmailVerification,
    PasswordReset,
    RefreshToken,
)
from app.models.location import (  # noqa: F401
    AppConfig,
    City,
    Country,
    Currency,
    VisaRule,
)
from app.models.billing import (  # noqa: F401
    Payment,
    Plan,
    PlanFeature,
    Subscription,
    UsageCounter,
)
from app.models.chat import AIRequest, ChatConversation, ChatMessage  # noqa: F401
from app.models.document import (  # noqa: F401
    Document,
    DocumentAnalysis,
    DocumentFile,
    ExtractedField,
)
from app.models.travel import Trip, TripItem  # noqa: F401
from app.models.user import (  # noqa: F401
    Permission,
    Role,
    User,
    role_permissions,
    user_roles,
)

__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "user_roles",
    "role_permissions",
    "RefreshToken",
    "EmailVerification",
    "PasswordReset",
    "Currency",
    "Country",
    "City",
    "VisaRule",
    "AppConfig",
    "Trip",
    "TripItem",
    "ChatConversation",
    "ChatMessage",
    "AIRequest",
    "Document",
    "DocumentFile",
    "DocumentAnalysis",
    "ExtractedField",
    "Plan",
    "PlanFeature",
    "Subscription",
    "UsageCounter",
    "Payment",
    "AuditLog",
]
