"""
Modelos de sincronización con calendarios externos.

CalendarConnection — una conexión por usuario por proveedor (google/apple).
SyncLog           — registro de cada sincronización ejecutada.

EXTENSIÓN FUTURA — Recordatorios:
    El campo sync_reminders existe pero siempre es False.
    Cuando se implemente Google Tasks / Apple Reminders, activar este campo
    y añadir la lógica en sync_service.py.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core import Base


class CalendarConnection(Base):
    __tablename__  = "calendar_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
        {"schema": "calendar_tracker"},
    )

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider         = Column(String(20), nullable=False)

    # Tokens OAuth (Google) o credenciales CalDAV (Apple)
    access_token     = Column(String,  nullable=True)
    refresh_token    = Column(String,  nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    caldav_username  = Column(String,  nullable=True)
    caldav_password  = Column(String,  nullable=True)

    calendar_id      = Column(String,  nullable=True)

    # Qué sincronizar
    sync_events      = Column(Boolean, default=True,  nullable=False)
    sync_routines    = Column(Boolean, default=True,  nullable=False)
    sync_reminders   = Column(Boolean, default=False, nullable=False)  # EXTENSIÓN FUTURA

    is_active        = Column(Boolean, default=True,  nullable=False)
    last_synced_at   = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user      = relationship("User",    back_populates="calendar_connections")
    sync_logs = relationship("SyncLog", back_populates="connection", cascade="all, delete-orphan")


class SyncLog(Base):
    __tablename__  = "sync_logs"
    __table_args__ = {"schema": "calendar_tracker"}

    id            = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("calendar_tracker.calendar_connections.id", ondelete="CASCADE"), nullable=False)
    user_id       = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider      = Column(String(20), nullable=False)
    direction     = Column(String(10), nullable=False)  # "inbound" | "outbound" | "both"

    events_created  = Column(Integer, default=0)
    events_updated  = Column(Integer, default=0)
    events_deleted  = Column(Integer, default=0)
    routines_synced = Column(Integer, default=0)
    error           = Column(String, nullable=True)
    synced_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user       = relationship("User",               back_populates="sync_logs")
    connection = relationship("CalendarConnection", back_populates="sync_logs")