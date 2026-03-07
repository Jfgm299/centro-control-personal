"""
Sincronización bidireccional con Google Calendar — last-write-wins.

Flujo por evento:
  - Existe en ambos lados (tiene google_event_id):
      · Google más reciente  → actualizar local   (pull)
      · Local más reciente   → actualizar Google  (push)
      · Sin timestamps       → Google gana (comportamiento conservador)
  - Solo en local (sin google_event_id) → crear en Google
  - Solo en Google (sin evento local)   → crear en local
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection
from app.modules.calendar_tracker.models.event import Event
from app.modules.calendar_tracker.integrations.google.client import GoogleCalendarClient
from app.modules.calendar_tracker.integrations.google.mapper import (
    event_to_google,
    google_to_event_data,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class GoogleCalendarSync:

    def sync_events(self, connection: CalendarConnection, db: Session) -> dict:
        """
        Sync bidireccional con resolución de conflictos last-write-wins.
        Sustituye a push_events + pull_events independientes.
        """
        client     = GoogleCalendarClient(connection, db)
        result     = {"events_created": 0, "events_updated": 0, "events_deleted": 0}
        now        = datetime.now(timezone.utc)
        look_ahead = now + timedelta(days=30)

        # ── 1. Obtener eventos de Google ──────────────────────────────────────
        google_events = client.list_events(now, look_ahead)
        google_by_id  = {}  # google_event_id → parsed data
        for g_ev in google_events:
            data = google_to_event_data(g_ev)
            if data and data["google_event_id"]:
                google_by_id[data["google_event_id"]] = data

        # ── 2. Obtener eventos locales futuros ────────────────────────────────
        local_events = db.query(Event).filter(
            Event.user_id      == connection.user_id,
            Event.is_cancelled == False,
            Event.start_at     >= now,
            Event.start_at     <= look_ahead,
        ).all()

        processed_google_ids = set()

        # ── 3. Resolver conflictos para eventos que existen en ambos lados ───
        for event in local_events:
            try:
                if event.google_event_id and event.google_event_id in google_by_id:
                    # Evento existe en ambos — comparar timestamps
                    processed_google_ids.add(event.google_event_id)
                    g_data       = google_by_id[event.google_event_id]
                    google_ts    = _ensure_utc(g_data["google_updated_at"])
                    local_ts     = _ensure_utc(event.updated_at or event.created_at)

                    if google_ts and local_ts and google_ts > local_ts:
                        # Google es más reciente → actualizar local
                        event.title       = g_data["title"]
                        event.description = g_data["description"]
                        event.start_at    = g_data["start_at"]
                        event.end_at      = g_data["end_at"]
                        db.commit()
                        result["events_updated"] += 1
                    else:
                        # Local es más reciente (o no hay timestamps) → actualizar Google
                        body = event_to_google(event)
                        client.update_event(event.google_event_id, body)
                        result["events_updated"] += 1

                elif not event.google_event_id:
                    # Solo en local → crear en Google
                    body         = event_to_google(event)
                    g_ev         = client.create_event(body)
                    event.google_event_id = g_ev["id"]
                    db.commit()
                    result["events_created"] += 1

                # Si tiene google_event_id pero ya no está en Google → ignorar
                # (fue borrado en Google; no borramos local automáticamente)

            except Exception:
                continue

        # ── 4. Eventos que solo existen en Google → crear en local ────────────
        for gid, g_data in google_by_id.items():
            if gid in processed_google_ids:
                continue
            try:
                event = Event(
                    user_id         = connection.user_id,
                    title           = g_data["title"],
                    description     = g_data["description"],
                    start_at        = g_data["start_at"],
                    end_at          = g_data["end_at"],
                    google_event_id = gid,
                )
                db.add(event)
                db.commit()
                result["events_created"] += 1
            except Exception:
                continue

        return result

    # Mantener push/pull como alias por compatibilidad con sync_service
    def push_events(self, connection: CalendarConnection, db: Session) -> dict:
        return self.sync_events(connection, db)

    def pull_events(self, connection: CalendarConnection, db: Session) -> dict:
        return {"events_created": 0, "events_updated": 0, "events_deleted": 0}

    def validate_connection(self, connection: CalendarConnection, db: Session) -> bool:
        try:
            client = GoogleCalendarClient(connection, db)
            client.list_calendars()
            return True
        except Exception:
            return False


google_sync = GoogleCalendarSync()