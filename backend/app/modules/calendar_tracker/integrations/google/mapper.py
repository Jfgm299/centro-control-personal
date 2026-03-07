"""
Conversión entre nuestros modelos (Event, Routine) y el formato de Google Calendar.
"""
from datetime import datetime, timezone
from typing import Optional
from app.modules.calendar_tracker.models.event   import Event
from app.modules.calendar_tracker.models.routine import Routine


def event_to_google(event: Event) -> dict:
    """Convierte nuestro Event al formato de Google Calendar."""
    body = {
        "summary":     event.title,
        "description": event.description or "",
        "start": {"dateTime": event.start_at.isoformat(), "timeZone": "UTC"},
        "end":   {"dateTime": event.end_at.isoformat(),   "timeZone": "UTC"},
    }
    if event.reminder_minutes:
        body["reminders"] = {
            "useDefault": False,
            "overrides":  [{"method": "popup", "minutes": event.reminder_minutes}],
        }
    else:
        body["reminders"] = {"useDefault": False, "overrides": []}

    return body


def google_to_event_data(google_event: dict) -> Optional[dict]:
    """
    Convierte un evento de Google Calendar a datos para crear/actualizar nuestro Event.
    Devuelve None si el evento no tiene fechas válidas (ej: eventos de día completo sin hora).
    """
    start = google_event.get("start", {})
    end   = google_event.get("end",   {})

    start_dt = start.get("dateTime")
    end_dt   = end.get("dateTime")

    if not start_dt or not end_dt:
        return None  # evento de día completo sin hora — ignorar por ahora

    return {
        "title":           google_event.get("summary", "Sin título"),
        "description":     google_event.get("description"),
        "start_at":        datetime.fromisoformat(start_dt),
        "end_at":          datetime.fromisoformat(end_dt),
        "google_event_id": google_event.get("id"),
    }


def routine_to_google(routine: Routine, occurrence_date: str) -> dict:
    """
    Convierte una Routine a un evento de Google Calendar para una fecha concreta.
    occurrence_date: 'YYYY-MM-DD'
    """
    start_iso = f"{occurrence_date}T{routine.start_time.strftime('%H:%M:%S')}+00:00"
    end_iso   = f"{occurrence_date}T{routine.end_time.strftime('%H:%M:%S')}+00:00"

    return {
        "summary": routine.title,
        "start":   {"dateTime": start_iso, "timeZone": "UTC"},
        "end":     {"dateTime": end_iso,   "timeZone": "UTC"},
        "recurrence": [f"RRULE:{routine.rrule}"],
    }