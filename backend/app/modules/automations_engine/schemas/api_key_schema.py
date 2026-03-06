from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from ..enums import ApiKeyScope


class ApiKeyCreate(BaseModel):
    name:          str = Field(min_length=1, max_length=100)
    automation_id: Optional[int] = None
    scopes:        list[ApiKeyScope] = Field(default_factory=lambda: [ApiKeyScope.TRIGGER])
    expires_at:    Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            int
    name:          str
    automation_id: Optional[int]
    key_prefix:    str
    scopes:        list[str]
    last_used_at:  Optional[datetime]
    expires_at:    Optional[datetime]
    is_active:     bool
    created_at:    datetime


class ApiKeyCreateResponse(ApiKeyResponse):
    """Solo se devuelve en la creación — incluye el token en claro."""
    token: str