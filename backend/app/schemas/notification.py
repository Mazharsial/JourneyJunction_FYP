"""Notification & preference schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    channel: str
    event: str
    recipient: str
    body: str
    provider: str
    status: str
    created_at: datetime


class PreferencesUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    phone_number: str | None = Field(default=None, max_length=32)
    whatsapp_opt_in: bool | None = None
    email_opt_in: bool | None = None


class PreferencesOut(BaseModel):
    full_name: str
    phone_number: str
    whatsapp_opt_in: bool
    email_opt_in: bool
    whatsapp_enabled: bool  # server has WhatsApp configured
    email_enabled: bool     # server has Klaviyo configured


class TestSendRequest(BaseModel):
    channel: str = Field(pattern="^(whatsapp|email)$")
    message: str = Field(min_length=1, max_length=1000)
