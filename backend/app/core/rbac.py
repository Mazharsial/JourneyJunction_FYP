"""
RBAC catalogue: canonical role names, permission codes, and the default
role-to-permission mapping. Seeded into the database (see app/db/seed.py);
roles/permissions remain data-driven and editable by admins at runtime.
"""
from __future__ import annotations


class Roles:
    TRAVELER = "traveler"
    STAFF = "staff"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Perms:
    # Travel / documents (self-service)
    TRIP_MANAGE = "trip:manage"
    DOCUMENT_MANAGE = "document:manage"
    CHATBOT_USE = "chatbot:use"
    SUBSCRIPTION_MANAGE = "subscription:manage"
    # Support
    SUPPORT_VIEW = "support:view"
    # Admin
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"
    PLAN_MANAGE = "plan:manage"
    CONFIG_MANAGE = "config:manage"
    AUDIT_VIEW = "audit:view"


PERMISSION_DESCRIPTIONS: dict[str, str] = {
    Perms.TRIP_MANAGE: "Create and manage own trips/itineraries",
    Perms.DOCUMENT_MANAGE: "Upload and manage own travel documents",
    Perms.CHATBOT_USE: "Use the AI travel assistant",
    Perms.SUBSCRIPTION_MANAGE: "Manage own subscription",
    Perms.SUPPORT_VIEW: "View support-related user data",
    Perms.USER_MANAGE: "Manage users",
    Perms.ROLE_MANAGE: "Manage roles and permissions",
    Perms.PLAN_MANAGE: "Manage subscription plans",
    Perms.CONFIG_MANAGE: "Manage application/market configuration",
    Perms.AUDIT_VIEW: "View audit logs",
}

_SELF_SERVICE = [
    Perms.TRIP_MANAGE,
    Perms.DOCUMENT_MANAGE,
    Perms.CHATBOT_USE,
    Perms.SUBSCRIPTION_MANAGE,
]

_ADMIN = [
    Perms.USER_MANAGE,
    Perms.ROLE_MANAGE,
    Perms.PLAN_MANAGE,
    Perms.CONFIG_MANAGE,
    Perms.AUDIT_VIEW,
]

# Default role -> permission codes.
ROLE_PERMISSIONS: dict[str, list[str]] = {
    Roles.TRAVELER: list(_SELF_SERVICE),
    Roles.STAFF: [*_SELF_SERVICE, Perms.SUPPORT_VIEW],
    Roles.ADMIN: [*_SELF_SERVICE, Perms.SUPPORT_VIEW, *_ADMIN],
    Roles.SUPER_ADMIN: list(PERMISSION_DESCRIPTIONS.keys()),
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    Roles.TRAVELER: "Standard customer who plans trips and verifies documents",
    Roles.STAFF: "Support operator",
    Roles.ADMIN: "Administrator",
    Roles.SUPER_ADMIN: "Full system administrator",
}

DEFAULT_SIGNUP_ROLE = Roles.TRAVELER
