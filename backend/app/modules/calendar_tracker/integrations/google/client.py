"""
Cliente HTTP para Google Calendar API.

Gestiona automáticamente la renovación del access_token cuando expira.
"""
from datetime import datetime, timezone
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection
from app.modules.calendar_tracker.integrations.google.auth import refresh_access_token

GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"


class GoogleCalendarClient:

    def __init__(self, connection: CalendarConnection, db: Session):
        self.connection = connection
        self.db         = db
        self._ensure_token_fresh()

    def _ensure_token_fresh(self) -> None:
        """Renueva el access_token si está a menos de 5 minutos de expirar."""
        if not self.connection.token_expires_at:
            return
        now = datetime.now(timezone.utc)
        expires_at = self.connection.token_expires_at
        if expires_at.tzinfo is None:
            from datetime import timezone as tz
            expires_at = expires_at.replace(tzinfo=tz.utc)

        if (expires_at - now).total_seconds() < 300:
            tokens = refresh_access_token(self.connection.refresh_token)
            self.connection.access_token     = tokens["access_token"]
            self.connection.token_expires_at = tokens["expires_at"]
            self.db.commit()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.connection.access_token}"}

    def _calendar_id(self) -> str:
        return self.connection.calendar_id or "primary"

    def list_events(self, time_min: datetime, time_max: datetime) -> list[dict]:
        """Lista eventos de Google Calendar en el rango dado."""
        response = httpx.get(
            f"{GOOGLE_CALENDAR_API}/calendars/{self._calendar_id()}/events",
            headers=self._headers(),
            params={
                "timeMin":    time_min.isoformat(),
                "timeMax":    time_max.isoformat(),
                "singleEvents": "true",
                "orderBy":    "startTime",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("items", [])

    def create_event(self, event_body: dict) -> dict:
        """Crea un evento en Google Calendar."""
        response = httpx.post(
            f"{GOOGLE_CALENDAR_API}/calendars/{self._calendar_id()}/events",
            headers=self._headers(),
            json=event_body,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def update_event(self, google_event_id: str, event_body: dict) -> dict:
        """Actualiza un evento existente en Google Calendar."""
        response = httpx.put(
            f"{GOOGLE_CALENDAR_API}/calendars/{self._calendar_id()}/events/{google_event_id}",
            headers=self._headers(),
            json=event_body,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def delete_event(self, google_event_id: str) -> None:
        """Elimina un evento de Google Calendar."""
        response = httpx.delete(
            f"{GOOGLE_CALENDAR_API}/calendars/{self._calendar_id()}/events/{google_event_id}",
            headers=self._headers(),
            timeout=10,
        )
        if response.status_code != 404:
            response.raise_for_status()

    def list_calendars(self) -> list[dict]:
        """Lista los calendarios disponibles del usuario."""
        response = httpx.get(
            f"{GOOGLE_CALENDAR_API}/users/me/calendarList",
            headers=self._headers(),
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("items", [])