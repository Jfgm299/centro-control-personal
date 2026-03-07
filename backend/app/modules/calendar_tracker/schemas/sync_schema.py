from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CalendarConnectionCreate(BaseModel):
    provider:       str
    calendar_id:    Optional[str]  = None
    sync_events:    bool           = True
    sync_routines:  bool           = True
    # sync_reminders omitido intencionalmente — EXTENSIÓN FUTURA


class CalendarConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    provider:        str
    calendar_id:     Optional[str]
    sync_events:     bool
    sync_routines:   bool
    sync_reminders:  bool
    is_active:       bool
    last_synced_at:  Optional[datetime]
    created_at:      datetime


class SyncLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    provider:        str
    direction:       str
    events_created:  int
    events_updated:  int
    events_deleted:  int
    routines_synced: int
    error:           Optional[str]
    synced_at:       datetime


class GoogleOAuthCallbackParams(BaseModel):
    code:  str
    state: Optional[str] = None


class AppleConnectRequest(BaseModel):
    username:    str   # Apple ID email
    password:    str   # App-specific password
    calendar_id: Optional[str] = None
    sync_events:   bool = True
    sync_routines: bool = True


class ManualSyncResponse(BaseModel):
    provider:        str
    direction:       str
    events_created:  int
    events_updated:  int
    events_deleted:  int
    routines_synced: int
    error:           Optional[str] = None