"""
Orquestador de sincronización con calendarios externos.

Gestiona CalendarConnections y coordina Google/Apple sync.

EXTENSIÓN FUTURA — Recordatorios:
    Cuando connection.sync_reminders sea True, añadir llamadas a
    google_tasks_sync o apple_reminders_sync aquí.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection, SyncLog
from app.modules.calendar_tracker.integrations.google.sync import google_sync
from app.modules.calendar_tracker.integrations.apple.sync  import apple_sync
from app.modules.calendar_tracker.integrations.apple.auth  import encrypt


class SyncService:

    # ── Conexiones ────────────────────────────────────────────────────────────

    def get_connections(self, user_id: int, db: Session) -> list[CalendarConnection]:
        return db.query(CalendarConnection).filter(
            CalendarConnection.user_id  == user_id,
            CalendarConnection.is_active == True,
        ).all()

    def get_connection(self, user_id: int, provider: str, db: Session) -> CalendarConnection | None:
        return db.query(CalendarConnection).filter(
            CalendarConnection.user_id  == user_id,
            CalendarConnection.provider == provider,
            CalendarConnection.is_active == True,
        ).first()

    def create_google_connection(
        self,
        user_id:       int,
        access_token:  str,
        refresh_token: str,
        expires_at:    datetime,
        calendar_id:   str | None,
        sync_events:   bool,
        sync_routines: bool,
        db:            Session,
    ) -> CalendarConnection:
        # Si ya existe una conexión para este usuario y proveedor, la actualizamos
        existing = db.query(CalendarConnection).filter(
            CalendarConnection.user_id  == user_id,
            CalendarConnection.provider == "google",
        ).first()

        if existing:
            existing.access_token     = access_token
            existing.refresh_token    = refresh_token
            existing.token_expires_at = expires_at
            existing.calendar_id      = calendar_id
            existing.sync_events      = sync_events
            existing.sync_routines    = sync_routines
            existing.is_active        = True
            db.commit()
            db.refresh(existing)
            return existing

        connection = CalendarConnection(
            user_id          = user_id,
            provider         = "google",
            access_token     = access_token,
            refresh_token    = refresh_token,
            token_expires_at = expires_at,
            calendar_id      = calendar_id,
            sync_events      = sync_events,
            sync_routines    = sync_routines,
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)
        return connection

    def create_apple_connection(
        self,
        user_id:       int,
        username:      str,
        password:      str,
        calendar_id:   str | None,
        sync_events:   bool,
        sync_routines: bool,
        db:            Session,
    ) -> CalendarConnection:
        existing = db.query(CalendarConnection).filter(
            CalendarConnection.user_id  == user_id,
            CalendarConnection.provider == "apple",
        ).first()

        encrypted_password = encrypt(password)

        if existing:
            existing.caldav_username = username
            existing.caldav_password = encrypted_password
            existing.calendar_id     = calendar_id
            existing.sync_events     = sync_events
            existing.sync_routines   = sync_routines
            existing.is_active       = True
            db.commit()
            db.refresh(existing)
            return existing

        connection = CalendarConnection(
            user_id         = user_id,
            provider        = "apple",
            caldav_username = username,
            caldav_password = encrypted_password,
            calendar_id     = calendar_id,
            sync_events     = sync_events,
            sync_routines   = sync_routines,
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)
        return connection

    def disconnect(self, user_id: int, provider: str, db: Session) -> bool:
        connection = self.get_connection(user_id, provider, db)
        if not connection:
            return False
        connection.is_active = False
        db.commit()
        return True

    # ── Sincronización ────────────────────────────────────────────────────────

    def sync(self, connection: CalendarConnection, db: Session) -> SyncLog:
        """Ejecuta sync bidireccional para una conexión y guarda el log."""
        result = {
            "events_created": 0,
            "events_updated": 0,
            "events_deleted": 0,
            "routines_synced": 0,
            "error": None,
        }

        try:
            if connection.provider == "google":
                syncer = google_sync
            else:
                syncer = apple_sync

            if connection.sync_events:
                pull = syncer.pull_events(connection, db)
                push = syncer.push_events(connection, db)
                result["events_created"] += pull["events_created"] + push["events_created"]
                result["events_updated"] += pull["events_updated"] + push["events_updated"]
                result["events_deleted"] += pull["events_deleted"] + push["events_deleted"]

            # EXTENSIÓN FUTURA — Recordatorios:
            # if connection.sync_reminders:
            #     pass

            connection.last_synced_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as e:
            result["error"] = str(e)

        log = SyncLog(
            connection_id   = connection.id,
            user_id         = connection.user_id,
            provider        = connection.provider,
            direction       = "both",
            events_created  = result["events_created"],
            events_updated  = result["events_updated"],
            events_deleted  = result["events_deleted"],
            routines_synced = result["routines_synced"],
            error           = result["error"],
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def get_logs(self, user_id: int, provider: str, db: Session) -> list[SyncLog]:
        connection = self.get_connection(user_id, provider, db)
        if not connection:
            return []
        return (
            db.query(SyncLog)
            .filter(SyncLog.connection_id == connection.id)
            .order_by(SyncLog.synced_at.desc())
            .limit(50)
            .all()
        )


sync_service = SyncService()