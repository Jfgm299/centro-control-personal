"""
Sincronización bidireccional con Apple Calendar via CalDAV — last-write-wins.

Flujo por evento:
  - Existe en ambos lados (tiene apple_event_id):
      · Apple más reciente  → actualizar local   (LAST-MODIFIED > updated_at)
      · Local más reciente  → actualizar Apple   (updated_at > LAST-MODIFIED)
      · Sin timestamps      → Apple gana (comportamiento conservador)
  - Solo en local (sin apple_event_id) → crear en Apple
  - Solo en Apple (sin evento local)   → crear en local
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection
from app.modules.calendar_tracker.models.event import Event
from app.modules.calendar_tracker.integrations.apple.auth import decrypt
from app.modules.calendar_tracker.integrations.apple.client import AppleCalendarClient
from app.modules.calendar_tracker.integrations.apple.mapper import event_to_ical, ical_to_event_data


def _ensure_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class AppleCalendarSync:

    def _get_client(self, connection: CalendarConnection) -> AppleCalendarClient:
        username = connection.caldav_username
        password = decrypt(connection.caldav_password)
        return AppleCalendarClient(
            username=username,
            password=password,
            calendar_id=connection.calendar_id,
        )

    def sync_events(self, connection: CalendarConnection, db: Session) -> dict:
        """
        Sync bidireccional con resolución de conflictos last-write-wins.
        Sustituye a push_events + pull_events independientes.
        """
        client     = self._get_client(connection)
        result     = {"events_created": 0, "events_updated": 0, "events_deleted": 0}
        now        = datetime.now(timezone.utc)
        look_ahead = now + timedelta(days=30)

        # ── 1. Obtener eventos de Apple ───────────────────────────────────────
        apple_events = client.list_events(now, look_ahead)
        apple_by_uid = {}  # apple_event_id (UID) → parsed data
        for a_ev in apple_events:
            data = ical_to_event_data(a_ev)
            if data and data["apple_event_id"]:
                apple_by_uid[data["apple_event_id"]] = data

        # ── 2. Obtener eventos locales futuros ────────────────────────────────
        local_events = db.query(Event).filter(
            Event.user_id      == connection.user_id,
            Event.is_cancelled == False,
            Event.start_at     >= now,
            Event.start_at     <= look_ahead,
        ).all()

        processed_apple_ids = set()

        # ── 3. Resolver conflictos para eventos que existen en ambos lados ───
        for event in local_events:
            try:
                if event.apple_event_id and event.apple_event_id in apple_by_uid:
                    # Evento existe en ambos — comparar timestamps
                    processed_apple_ids.add(event.apple_event_id)
                    a_data    = apple_by_uid[event.apple_event_id]
                    apple_ts  = _ensure_utc(a_data["apple_updated_at"])
                    local_ts  = _ensure_utc(event.updated_at or event.created_at)

                    if apple_ts and local_ts and apple_ts > local_ts:
                        # Apple es más reciente → actualizar local
                        event.title       = a_data["title"]
                        event.description = a_data["description"]
                        event.start_at    = a_data["start_at"]
                        event.end_at      = a_data["end_at"]
                        db.commit()
                        result["events_updated"] += 1
                    else:
                        # Local es más reciente (o sin timestamps) → actualizar Apple
                        ical = event_to_ical(event)
                        client.update_event(event.apple_event_id, ical)
                        result["events_updated"] += 1

                elif not event.apple_event_id:
                    # Solo en local → crear en Apple
                    ical    = event_to_ical(event)
                    created = client.create_event(ical)
                    event.apple_event_id = str(created.url).split("/")[-1].replace(".ics", "")
                    db.commit()
                    result["events_created"] += 1

                # Si tiene apple_event_id pero ya no está en Apple → ignorar

            except Exception:
                continue

        # ── 4. Eventos que solo existen en Apple → crear en local ─────────────
        for uid, a_data in apple_by_uid.items():
            if uid in processed_apple_ids:
                continue
            try:
                event = Event(
                    user_id        = connection.user_id,
                    title          = a_data["title"],
                    description    = a_data["description"],
                    start_at       = a_data["start_at"],
                    end_at         = a_data["end_at"],
                    apple_event_id = uid,
                )
                db.add(event)
                db.commit()
                result["events_created"] += 1
            except Exception:
                continue

        return result

    # Alias por compatibilidad con sync_service
    def push_events(self, connection: CalendarConnection, db: Session) -> dict:
        return self.sync_events(connection, db)

    def pull_events(self, connection: CalendarConnection, db: Session) -> dict:
        return {"events_created": 0, "events_updated": 0, "events_deleted": 0}

    def validate_connection(self, connection: CalendarConnection, db: Session) -> bool:
        try:
            client = self._get_client(connection)
            client.list_calendars()
            return True
        except Exception:
            return False


apple_sync = AppleCalendarSync()