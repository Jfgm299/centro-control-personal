"""
Lógica de sincronización bidireccional con Google Calendar.

push_events()  — nuestra DB → Google Calendar
pull_events()  — Google Calendar → nuestra DB
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection, SyncLog
from app.modules.calendar_tracker.models.event import Event
from app.modules.calendar_tracker.integrations.google.client import GoogleCalendarClient
from app.modules.calendar_tracker.integrations.google.mapper import (
    event_to_google,
    google_to_event_data,
)


class GoogleCalendarSync:

    def push_events(self, connection: CalendarConnection, db: Session) -> dict:
        """Exporta eventos de nuestra DB a Google Calendar."""
        client = GoogleCalendarClient(connection, db)
        result = {"events_created": 0, "events_updated": 0, "events_deleted": 0}

        now     = datetime.now(timezone.utc)
        look_ahead = now + timedelta(days=30)

        events = db.query(Event).filter(
            Event.user_id      == connection.user_id,
            Event.is_cancelled == False,
            Event.start_at     >= now,
            Event.start_at     <= look_ahead,
        ).all()

        for event in events:
            try:
                body = event_to_google(event)
                if event.google_event_id:
                    client.update_event(event.google_event_id, body)
                    result["events_updated"] += 1
                else:
                    google_event = client.create_event(body)
                    event.google_event_id = google_event["id"]
                    db.commit()
                    result["events_created"] += 1
            except Exception:
                continue

        return result

    def pull_events(self, connection: CalendarConnection, db: Session) -> dict:
        """Importa eventos de Google Calendar a nuestra DB."""
        client = GoogleCalendarClient(connection, db)
        result = {"events_created": 0, "events_updated": 0, "events_deleted": 0}

        now        = datetime.now(timezone.utc)
        look_ahead = now + timedelta(days=30)

        google_events = client.list_events(now, look_ahead)

        for g_event in google_events:
            try:
                data = google_to_event_data(g_event)
                if not data:
                    continue

                existing = db.query(Event).filter(
                    Event.user_id        == connection.user_id,
                    Event.google_event_id == data["google_event_id"],
                ).first()

                if existing:
                    existing.title       = data["title"]
                    existing.description = data["description"]
                    existing.start_at    = data["start_at"]
                    existing.end_at      = data["end_at"]
                    db.commit()
                    result["events_updated"] += 1
                else:
                    event = Event(
                        user_id          = connection.user_id,
                        title            = data["title"],
                        description      = data["description"],
                        start_at         = data["start_at"],
                        end_at           = data["end_at"],
                        google_event_id  = data["google_event_id"],
                    )
                    db.add(event)
                    db.commit()
                    result["events_created"] += 1
            except Exception:
                continue

        return result

    def validate_connection(self, connection: CalendarConnection, db: Session) -> bool:
        try:
            client = GoogleCalendarClient(connection, db)
            client.list_calendars()
            return True
        except Exception:
            return False


google_sync = GoogleCalendarSync()