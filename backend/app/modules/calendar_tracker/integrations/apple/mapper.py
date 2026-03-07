"""
Conversión entre nuestros modelos (Event) y formato iCal (VEVENT).
"""
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.modules.calendar_tracker.models.event import Event


def event_to_ical(event: Event) -> str:
    """Convierte nuestro Event a un string iCal (VEVENT)."""
    uid     = event.apple_event_id or str(uuid.uuid4())
    start   = event.start_at.strftime("%Y%m%dT%H%M%SZ")
    end     = event.end_at.strftime("%Y%m%dT%H%M%SZ")
    summary = event.title.replace("\n", " ")
    desc    = (event.description or "").replace("\n", " ")

    # LAST-MODIFIED refleja cuándo lo editamos nosotros — clave para conflict resolution
    last_modified = (event.updated_at or event.created_at).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Sistema Personal//Calendar//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"SUMMARY:{summary}",
        f"DTSTART:{start}",
        f"DTEND:{end}",
        f"LAST-MODIFIED:{last_modified}",
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
    Incluye apple_updated_at (LAST-MODIFIED del iCal) para conflict resolution.
    Devuelve None si no se puede parsear.
    """
    try:
        from icalendar import Calendar
        cal    = Calendar.from_ical(caldav_event.data)
        vevent = next((c for c in cal.walk() if c.name == "VEVENT"), None)
        if not vevent:
            return None

        start = vevent.get("DTSTART").dt
        end   = vevent.get("DTEND").dt

        # Ignorar eventos de día completo sin hora
        if not hasattr(start, "hour"):
            return None

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        # LAST-MODIFIED → para last-write-wins
        apple_updated_at = None
        last_modified = vevent.get("LAST-MODIFIED")
        if last_modified:
            try:
                dt = last_modified.dt
                if hasattr(dt, "hour"):
                    apple_updated_at = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass

        uid = str(vevent.get("UID", ""))

        return {
            "title":            str(vevent.get("SUMMARY", "Sin título")),
            "description":      str(vevent.get("DESCRIPTION", "")) or None,
            "start_at":         start,
            "end_at":           end,
            "apple_event_id":   uid,
            "apple_updated_at": apple_updated_at,  # para conflict resolution
        }
    except Exception:
        return None