"""
Lógica de sincronización bidireccional con Apple Calendar via CalDAV.

push_events()  — nuestra DB → Apple Calendar
pull_events()  — Apple Calendar → nuestra DB
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection
from app.modules.calendar_tracker.models.event import Event
from app.modules.calendar_tracker.integrations.apple.auth import decrypt
from app.modules.calendar_tracker.integrations.apple.client import AppleCalendarClient
from app.modules.calendar_tracker.integrations.apple.mapper import event_to_ical, ical_to_event_data


class AppleCalendarSync:

    def _get_client(self, connection: CalendarConnection) -> AppleCalendarClient:
        username = connection.caldav_username
        password = decrypt(connection.caldav_password)
        return AppleCalendarClient(
            username=username,
            password=password,
            calendar_id=connection.calendar_id,
        )

    def push_events(self, connection: CalendarConnection, db: Session) -> dict:
        """Exporta eventos de nuestra DB a Apple Calendar."""
        client = self._get_client(connection)
        result = {"events_created": 0, "events_updated": 0, "events_deleted": 0}

        now        = datetime.now(timezone.utc)
        look_ahead = now + timedelta(days=30)

        events = db.query(Event).filter(
            Event.user_id      == connection.user_id,
            Event.is_cancelled == False,
            Event.start_at     >= now,
            Event.start_at     <= look_ahead,
        ).all()

        for event in events:
            try:
                ical = event_to_ical(event)
                if event.apple_event_id:
                    client.update_event(event.apple_event_id, ical)
                    result["events_updated"] += 1
                else:
                    created = client.create_event(ical)
                    event.apple_event_id = str(created.url).split("/")[-1].replace(".ics", "")
                    db.commit()
                    result["events_created"] += 1
            except Exception:
                continue

        return result

    def pull_events(self, connection: CalendarConnection, db: Session) -> dict:
        """Importa eventos de Apple Calendar a nuestra DB."""
        client = self._get_client(connection)
        result = {"events_created": 0, "events_updated": 0, "events_deleted": 0}

        now        = datetime.now(timezone.utc)
        look_ahead = now + timedelta(days=30)

        apple_events = client.list_events(now, look_ahead)

        for a_event in apple_events:
            try:
                data = ical_to_event_data(a_event)
                if not data:
                    continue

                existing = db.query(Event).filter(
                    Event.user_id       == connection.user_id,
                    Event.apple_event_id == data["apple_event_id"],
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
                        user_id         = connection.user_id,
                        title           = data["title"],
                        description     = data["description"],
                        start_at        = data["start_at"],
                        end_at          = data["end_at"],
                        apple_event_id  = data["apple_event_id"],
                    )
                    db.add(event)
                    db.commit()
                    result["events_created"] += 1
            except Exception:
                continue

        return result

    def validate_connection(self, connection: CalendarConnection, db: Session) -> bool:
        try:
            client = self._get_client(connection)
            client.list_calendars()
            return True
        except Exception:
            return False


apple_sync = AppleCalendarSync()