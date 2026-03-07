"""
Conversión entre nuestros modelos (Event) y formato iCal (VEVENT).
"""
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.modules.calendar_tracker.models.event import Event


def event_to_ical(event: Event) -> str:
    """Convierte nuestro Event a un string iCal (VEVENT)."""
    uid      = event.apple_event_id or str(uuid.uuid4())
    start    = event.start_at.strftime("%Y%m%dT%H%M%SZ")
    end      = event.end_at.strftime("%Y%m%dT%H%M%SZ")
    summary  = event.title.replace("\n", " ")
    desc     = (event.description or "").replace("\n", " ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Centro Control//Calendar//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"SUMMARY:{summary}",
        f"DTSTART:{start}",
        f"DTEND:{end}",
    ]
    if desc:
        lines.append(f"DESCRIPTION:{desc}")
    if event.reminder_minutes:
        lines += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"TRIGGER:-PT{event.reminder_minutes}M",
            "END:VALARM",
        ]
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(lines)


def ical_to_event_data(caldav_event) -> Optional[dict]:
    """
    Convierte un evento CalDAV a datos para crear/actualizar nuestro Event.
    Devuelve None si no se puede parsear.
    """
    try:
        from icalendar import Calendar
        cal    = Calendar.from_ical(caldav_event.data)
        vevent = next(
            (c for c in cal.walk() if c.name == "VEVENT"),
            None
        )
        if not vevent:
            return None

        start = vevent.get("DTSTART").dt
        end   = vevent.get("DTEND").dt

        # Convertir date a datetime si es evento de día completo
        if not hasattr(start, "hour"):
            return None  # eventos de día completo — ignorar por ahora

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        uid = str(vevent.get("UID", ""))

        return {
            "title":          str(vevent.get("SUMMARY", "Sin título")),
            "description":    str(vevent.get("DESCRIPTION", "")) or None,
            "start_at":       start,
            "end_at":         end,
            "apple_event_id": uid,
        }
    except Exception:
        return None
