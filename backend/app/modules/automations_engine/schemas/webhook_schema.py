from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any


class WebhookCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                int
    automation_id:     int
    name:              str
    token:             str
    is_active:         bool
    last_triggered_at: Optional[datetime]
    created_at:        datetime


class WebhookInboundPayload(BaseModel):
    """Payload que recibe el endpoint público POST /webhooks/in/{token}"""
    source: Optional[str] = None
    data:   dict[str, Any] = Field(default_factory=dict)