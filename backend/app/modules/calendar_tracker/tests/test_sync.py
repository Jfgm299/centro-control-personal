"""
Tests de sincronización con Google Calendar y Apple Calendar.

Probamos:
1. Endpoints de conexión y desconexión
2. Sync manual (push/pull)
3. Lógica de sync_service
4. Mappers Google y Apple
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def google_tokens():
    return {
        "access_token":  "fake_access_token",
        "refresh_token": "fake_refresh_token",
        "expires_at":    datetime.now(timezone.utc) + timedelta(hours=1),
    }


@pytest.fixture
def google_connection(auth_client, db, google_tokens):
    """Crea una conexión Google real en la DB via sync_service."""
    from app.modules.calendar_tracker.services.sync_service import sync_service
    from app.core.auth.user import User

    user = db.query(User).filter(User.email == "test@test.com").first()
    return sync_service.create_google_connection(
        user_id       = user.id,
        access_token  = google_tokens["access_token"],
        refresh_token = google_tokens["refresh_token"],
        expires_at    = google_tokens["expires_at"],
        calendar_id   = "primary",
        sync_events   = True,
        sync_routines = True,
        db            = db,
    )


@pytest.fixture
def apple_connection(auth_client, db):
    """Crea una conexión Apple real en la DB via sync_service."""
    from app.modules.calendar_tracker.services.sync_service import sync_service
    from app.core.auth.user import User

    user = db.query(User).filter(User.email == "test@test.com").first()
    return sync_service.create_apple_connection(
        user_id       = user.id,
        username      = "test@icloud.com",
        password      = "test-app-password",
        calendar_id   = None,
        sync_events   = True,
        sync_routines = True,
        db            = db,
    )


@pytest.fixture
def future_event(auth_client, db):
    """Evento futuro real en la DB."""
    from app.core.auth.user import User
    from app.modules.calendar_tracker.models.event import Event

    user  = db.query(User).filter(User.email == "test@test.com").first()
    now   = datetime.now(timezone.utc)
    event = Event(
        user_id  = user.id,
        title    = "Evento de prueba",
        start_at = now + timedelta(hours=1),
        end_at   = now + timedelta(hours=2),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# ── Tests de endpoints ────────────────────────────────────────────────────────

class TestConnectionEndpoints:

    def test_google_connect_returns_auth_url(self, auth_client):
        with patch(
            "app.modules.calendar_tracker.routers.sync_router.authorize_url",
            return_value="https://accounts.google.com/o/oauth2/v2/auth?client_id=test"
        ):
            response = auth_client.post("/api/v1/calendar/integrations/google/connect")
        assert response.status_code == 200
        assert "auth_url" in response.json()
        assert "accounts.google.com" in response.json()["auth_url"]

    def test_google_callback_creates_connection(self, auth_client, db, google_tokens):
        with patch(
            "app.modules.calendar_tracker.routers.sync_router.exchange_code",
            return_value=google_tokens,
        ):
            response = auth_client.get(
                "/api/v1/calendar/integrations/google/callback",
                params={"code": "fake_code", "sync_events": True, "sync_routines": True},
            )
        assert response.status_code == 200

    def test_google_callback_invalid_code_fails(self, auth_client):
        with patch(
            "app.modules.calendar_tracker.routers.sync_router.exchange_code",
            side_effect=Exception("invalid_grant"),
        ):
            response = auth_client.get(
                "/api/v1/calendar/integrations/google/callback",
                params={"code": "bad_code"},
            )
        assert response.status_code == 400

    def test_apple_connect_creates_connection(self, auth_client, db):
        with patch(
            "app.modules.calendar_tracker.routers.sync_router.validate_credentials",
            return_value=True,
        ):
            response = auth_client.post(
                "/api/v1/calendar/integrations/apple/connect",
                json={
                "username":      "test@icloud.com",
                "password":      "test-app-password",
                "sync_events":   True,
                "sync_routines": True,
            },
        )
        assert response.status_code == 200

    def test_apple_connect_invalid_credentials_fails(self, auth_client):
        with patch(
            "app.modules.calendar_tracker.routers.sync_router.validate_credentials",
            return_value=False,
        ):
            response = auth_client.post(
            "/api/v1/calendar/integrations/apple/connect",
            json={"username": "bad@icloud.com", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_list_connections_empty(self, auth_client):
        """Sin conexiones devuelve lista vacía."""
        response = auth_client.get("/api/v1/calendar/integrations/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_connections_shows_active(self, auth_client, db, google_connection):
        """Lista las conexiones activas."""
        response = auth_client.get("/api/v1/calendar/integrations/")
        assert response.status_code == 200
        providers = [c["provider"] for c in response.json()]
        assert "google" in providers

    def test_disconnect_google(self, auth_client, db, google_connection):
        """DELETE /google/disconnect desactiva la conexión."""
        response = auth_client.delete("/api/v1/calendar/integrations/google/disconnect")
        assert response.status_code == 200
        assert response.json()["disconnected"] is True

        # Ya no aparece en la lista
        connections = auth_client.get("/api/v1/calendar/integrations/").json()
        providers = [c["provider"] for c in connections]
        assert "google" not in providers

    def test_disconnect_nonexistent_fails(self, auth_client):
        """Desconectar un provider sin conexión devuelve 404."""
        response = auth_client.delete("/api/v1/calendar/integrations/google/disconnect")
        assert response.status_code == 404

    def test_disconnect_invalid_provider_fails(self, auth_client):
        """Provider inválido devuelve 400."""
        response = auth_client.delete("/api/v1/calendar/integrations/microsoft/disconnect")
        assert response.status_code == 400

    def test_manual_sync_no_connection_fails(self, auth_client):
        """Sync manual sin conexión activa devuelve 404."""
        response = auth_client.post("/api/v1/calendar/integrations/google/sync")
        assert response.status_code == 404

    def test_manual_sync_google_returns_result(self, auth_client, db, google_connection):
        """Sync manual devuelve resultado con contadores."""
        with patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.pull_events",
            return_value={"events_created": 2, "events_updated": 1, "events_deleted": 0},
        ), patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.push_events",
            return_value={"events_created": 0, "events_updated": 1, "events_deleted": 0},
        ):
            response = auth_client.post("/api/v1/calendar/integrations/google/sync")

        assert response.status_code == 200
        body = response.json()
        assert body["provider"]       == "google"
        assert body["events_created"] == 2
        assert body["events_updated"] == 2

    def test_get_logs_empty(self, auth_client, db, google_connection):
        """Sin syncs previos devuelve lista vacía."""
        response = auth_client.get("/api/v1/calendar/integrations/google/logs")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_logs_after_sync(self, auth_client, db, google_connection):
        """Después de un sync aparece un log."""
        with patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.pull_events",
            return_value={"events_created": 1, "events_updated": 0, "events_deleted": 0},
        ), patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.push_events",
            return_value={"events_created": 0, "events_updated": 0, "events_deleted": 0},
        ):
            auth_client.post("/api/v1/calendar/integrations/google/sync")

        logs = auth_client.get("/api/v1/calendar/integrations/google/logs").json()
        assert len(logs) == 1
        assert logs[0]["provider"] == "google"


# ── Tests de sync_service ─────────────────────────────────────────────────────

class TestSyncService:

    def test_create_google_connection(self, auth_client, db, google_tokens):
        """create_google_connection crea una conexión en la DB."""
        from app.modules.calendar_tracker.services.sync_service import sync_service
        from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection
        from app.core.auth.user import User

        user = db.query(User).filter(User.email == "test@test.com").first()
        conn = sync_service.create_google_connection(
            user_id       = user.id,
            access_token  = google_tokens["access_token"],
            refresh_token = google_tokens["refresh_token"],
            expires_at    = google_tokens["expires_at"],
            calendar_id   = "primary",
            sync_events   = True,
            sync_routines = True,
            db            = db,
        )
        assert conn.id is not None
        assert conn.provider      == "google"
        assert conn.access_token  == "fake_access_token"
        assert conn.sync_events   is True
        assert conn.sync_reminders is False  # siempre False — EXTENSIÓN FUTURA

    def test_create_google_connection_updates_existing(self, auth_client, db, google_connection):
        """Crear una segunda conexión Google actualiza la existente."""
        from app.modules.calendar_tracker.services.sync_service import sync_service
        from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection
        from app.core.auth.user import User

        user = db.query(User).filter(User.email == "test@test.com").first()
        sync_service.create_google_connection(
            user_id       = user.id,
            access_token  = "new_token",
            refresh_token = "new_refresh",
            expires_at    = datetime.now(timezone.utc) + timedelta(hours=2),
            calendar_id   = "primary",
            sync_events   = True,
            sync_routines = True,
            db            = db,
        )

        connections = db.query(CalendarConnection).filter(
            CalendarConnection.user_id  == user.id,
            CalendarConnection.provider == "google",
        ).all()
        assert len(connections) == 1
        assert connections[0].access_token == "new_token"

    def test_create_apple_connection_encrypts_password(self, auth_client, db):
        """create_apple_connection encripta la contraseña en DB."""
        from app.modules.calendar_tracker.services.sync_service import sync_service
        from app.modules.calendar_tracker.integrations.apple.auth import decrypt
        from app.core.auth.user import User

        user = db.query(User).filter(User.email == "test@test.com").first()
        conn = sync_service.create_apple_connection(
            user_id       = user.id,
            username      = "test@icloud.com",
            password      = "my-secret-password",
            calendar_id   = None,
            sync_events   = True,
            sync_routines = True,
            db            = db,
        )

        assert conn.caldav_password != "my-secret-password"
        assert decrypt(conn.caldav_password) == "my-secret-password"

    def test_sync_creates_log(self, auth_client, db, google_connection):
        """sync() crea un SyncLog en la DB."""
        from app.modules.calendar_tracker.services.sync_service import sync_service
        from app.modules.calendar_tracker.models.calendar_sync import SyncLog

        with patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.pull_events",
            return_value={"events_created": 1, "events_updated": 0, "events_deleted": 0},
        ), patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.push_events",
            return_value={"events_created": 0, "events_updated": 0, "events_deleted": 0},
        ):
            log = sync_service.sync(google_connection, db)

        assert log.id            is not None
        assert log.provider      == "google"
        assert log.direction     == "both"
        assert log.events_created == 1
        assert log.error          is None

    def test_sync_updates_last_synced_at(self, auth_client, db, google_connection):
        """sync() actualiza last_synced_at de la conexión."""
        from app.modules.calendar_tracker.services.sync_service import sync_service

        before = google_connection.last_synced_at

        with patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.pull_events",
            return_value={"events_created": 0, "events_updated": 0, "events_deleted": 0},
        ), patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.push_events",
            return_value={"events_created": 0, "events_updated": 0, "events_deleted": 0},
        ):
            sync_service.sync(google_connection, db)

        db.refresh(google_connection)
        assert google_connection.last_synced_at is not None
        assert google_connection.last_synced_at != before

    def test_sync_logs_error_on_failure(self, auth_client, db, google_connection):
        """Si el sync falla, el error queda registrado en el SyncLog."""
        from app.modules.calendar_tracker.services.sync_service import sync_service

        with patch(
            "app.modules.calendar_tracker.integrations.google.sync.GoogleCalendarSync.pull_events",
            side_effect=Exception("API down"),
        ):
            log = sync_service.sync(google_connection, db)

        assert log.error is not None
        assert "API down" in log.error

    def test_disconnect_marks_inactive(self, auth_client, db, google_connection):
        """disconnect() marca la conexión como inactiva."""
        from app.modules.calendar_tracker.services.sync_service import sync_service
        from app.core.auth.user import User

        user = db.query(User).filter(User.email == "test@test.com").first()
        sync_service.disconnect(user.id, "google", db)

        db.refresh(google_connection)
        assert google_connection.is_active is False


# ── Tests de Google mapper ────────────────────────────────────────────────────

class TestGoogleMapper:

    def test_event_to_google_basic(self, db, future_event):
        """event_to_google convierte correctamente un evento básico."""
        from app.modules.calendar_tracker.integrations.google.mapper import event_to_google

        body = event_to_google(future_event)
        assert body["summary"] == "Evento de prueba"
        assert "dateTime" in body["start"]
        assert "dateTime" in body["end"]
        assert body["start"]["timeZone"] == "UTC"

    def test_event_to_google_with_reminder(self, db, future_event):
        """event_to_google incluye reminder como popup de Google."""
        from app.modules.calendar_tracker.integrations.google.mapper import event_to_google

        future_event.reminder_minutes = 15
        body = event_to_google(future_event)
        overrides = body["reminders"]["overrides"]
        assert len(overrides) == 1
        assert overrides[0]["minutes"] == 15
        assert overrides[0]["method"]  == "popup"

    def test_event_to_google_no_reminder(self, db, future_event):
        """Sin reminder, overrides está vacío."""
        from app.modules.calendar_tracker.integrations.google.mapper import event_to_google

        future_event.reminder_minutes = None
        body = event_to_google(future_event)
        assert body["reminders"]["overrides"] == []

    def test_google_to_event_data_basic(self):
        """google_to_event_data convierte un evento de Google correctamente."""
        from app.modules.calendar_tracker.integrations.google.mapper import google_to_event_data

        g_event = {
            "id":      "google_abc123",
            "summary": "Reunión de trabajo",
            "start":   {"dateTime": "2026-04-01T10:00:00+00:00"},
            "end":     {"dateTime": "2026-04-01T11:00:00+00:00"},
        }
        data = google_to_event_data(g_event)
        assert data is not None
        assert data["title"]           == "Reunión de trabajo"
        assert data["google_event_id"] == "google_abc123"
        assert data["start_at"].hour   == 10

    def test_google_to_event_data_all_day_returns_none(self):
        """Eventos de día completo (sin dateTime) devuelven None."""
        from app.modules.calendar_tracker.integrations.google.mapper import google_to_event_data

        g_event = {
            "id":      "google_allday",
            "summary": "Día festivo",
            "start":   {"date": "2026-04-01"},
            "end":     {"date": "2026-04-02"},
        }
        assert google_to_event_data(g_event) is None

    def test_google_to_event_data_no_summary(self):
        """Sin summary usa 'Sin título'."""
        from app.modules.calendar_tracker.integrations.google.mapper import google_to_event_data

        g_event = {
            "id":    "google_nosummary",
            "start": {"dateTime": "2026-04-01T10:00:00+00:00"},
            "end":   {"dateTime": "2026-04-01T11:00:00+00:00"},
        }
        data = google_to_event_data(g_event)
        assert data["title"] == "Sin título"


# ── Tests de Apple mapper ─────────────────────────────────────────────────────

class TestAppleMapper:

    def test_event_to_ical_basic(self, db, future_event):
        """event_to_ical genera un string iCal válido."""
        from app.modules.calendar_tracker.integrations.apple.mapper import event_to_ical

        ical = event_to_ical(future_event)
        assert "BEGIN:VCALENDAR" in ical
        assert "BEGIN:VEVENT"    in ical
        assert "END:VEVENT"      in ical
        assert "END:VCALENDAR"   in ical
        assert "Evento de prueba" in ical

    def test_event_to_ical_with_reminder(self, db, future_event):
        """event_to_ical incluye VALARM cuando hay reminder_minutes."""
        from app.modules.calendar_tracker.integrations.apple.mapper import event_to_ical

        future_event.reminder_minutes = 30
        ical = event_to_ical(future_event)
        assert "BEGIN:VALARM"   in ical
        assert "TRIGGER:-PT30M" in ical

    def test_event_to_ical_no_reminder(self, db, future_event):
        """Sin reminder no incluye VALARM."""
        from app.modules.calendar_tracker.integrations.apple.mapper import event_to_ical

        future_event.reminder_minutes = None
        ical = event_to_ical(future_event)
        assert "VALARM" not in ical

    def test_event_to_ical_uses_existing_uid(self, db, future_event):
        """Si el evento ya tiene apple_event_id lo usa como UID."""
        from app.modules.calendar_tracker.integrations.apple.mapper import event_to_ical

        future_event.apple_event_id = "existing-uid-123"
        ical = event_to_ical(future_event)
        assert "UID:existing-uid-123" in ical

    def test_ical_to_event_data_basic(self):
        """ical_to_event_data parsea un VEVENT correctamente."""
        from app.modules.calendar_tracker.integrations.apple.mapper import ical_to_event_data

        mock_event       = MagicMock()
        mock_event.data  = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "BEGIN:VEVENT\r\n"
            "UID:apple-uid-456\r\n"
            "SUMMARY:Cita médica\r\n"
            "DTSTART:20260401T100000Z\r\n"
            "DTEND:20260401T110000Z\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        data = ical_to_event_data(mock_event)
        assert data is not None
        assert data["title"]          == "Cita médica"
        assert data["apple_event_id"] == "apple-uid-456"
        assert data["start_at"].hour  == 10

    def test_ical_to_event_data_all_day_returns_none(self):
        """Eventos de día completo (DATE sin hora) devuelven None."""
        from app.modules.calendar_tracker.integrations.apple.mapper import ical_to_event_data

        mock_event      = MagicMock()
        mock_event.data = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "BEGIN:VEVENT\r\n"
            "UID:apple-allday\r\n"
            "SUMMARY:Día libre\r\n"
            "DTSTART;VALUE=DATE:20260401\r\n"
            "DTEND;VALUE=DATE:20260402\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        assert ical_to_event_data(mock_event) is None


# ── Tests de Google sync ──────────────────────────────────────────────────────

class TestGoogleSync:

    def test_push_events_creates_google_event(self, db, google_connection, future_event):
        """push_events crea el evento en Google y guarda el google_event_id."""
        from app.modules.calendar_tracker.integrations.google.sync import google_sync

        with patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient.create_event",
            return_value={"id": "google_new_123"},
        ), patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient._ensure_token_fresh",
        ):
            result = google_sync.push_events(google_connection, db)

        db.refresh(future_event)
        assert result["events_created"]   == 1
        assert future_event.google_event_id == "google_new_123"

    def test_push_events_updates_existing(self, db, google_connection, future_event):
        """push_events actualiza eventos que ya tienen google_event_id."""
        from app.modules.calendar_tracker.integrations.google.sync import google_sync

        future_event.google_event_id = "existing_google_id"
        db.commit()

        with patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient.update_event",
            return_value={"id": "existing_google_id"},
        ), patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient._ensure_token_fresh",
        ):
            result = google_sync.push_events(google_connection, db)

        assert result["events_updated"] == 1
        assert result["events_created"] == 0

    def test_pull_events_creates_local_event(self, db, google_connection):
        """pull_events crea un evento local desde Google."""
        from app.modules.calendar_tracker.integrations.google.sync import google_sync
        from app.modules.calendar_tracker.models.event import Event
        from app.core.auth.user import User

        user = db.query(User).filter(User.email == "test@test.com").first()

        google_events = [{
            "id":      "google_pulled_123",
            "summary": "Evento de Google",
            "start":   {"dateTime": "2026-04-01T10:00:00+00:00"},
            "end":     {"dateTime": "2026-04-01T11:00:00+00:00"},
        }]

        with patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient.list_events",
            return_value=google_events,
        ), patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient._ensure_token_fresh",
        ):
            result = google_sync.pull_events(google_connection, db)

        assert result["events_created"] == 1
        event = db.query(Event).filter(
            Event.user_id         == user.id,
            Event.google_event_id == "google_pulled_123",
        ).first()
        assert event is not None
        assert event.title == "Evento de Google"

    def test_pull_events_updates_existing(self, db, google_connection, future_event):
        """pull_events actualiza un evento local que ya existe."""
        from app.modules.calendar_tracker.integrations.google.sync import google_sync

        future_event.google_event_id = "google_existing_456"
        db.commit()

        google_events = [{
            "id":      "google_existing_456",
            "summary": "Título actualizado",
            "start":   {"dateTime": "2026-04-01T10:00:00+00:00"},
            "end":     {"dateTime": "2026-04-01T11:00:00+00:00"},
        }]

        with patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient.list_events",
            return_value=google_events,
        ), patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient._ensure_token_fresh",
        ):
            result = google_sync.pull_events(google_connection, db)

        db.refresh(future_event)
        assert result["events_updated"] == 1
        assert future_event.title       == "Título actualizado"

    def test_pull_events_skips_all_day(self, db, google_connection):
        """pull_events ignora eventos de día completo."""
        from app.modules.calendar_tracker.integrations.google.sync import google_sync
        from app.modules.calendar_tracker.models.event import Event
        from app.core.auth.user import User

        user = db.query(User).filter(User.email == "test@test.com").first()

        google_events = [{
            "id":      "google_allday",
            "summary": "Día festivo",
            "start":   {"date": "2026-04-01"},
            "end":     {"date": "2026-04-02"},
        }]

        with patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient.list_events",
            return_value=google_events,
        ), patch(
            "app.modules.calendar_tracker.integrations.google.client.GoogleCalendarClient._ensure_token_fresh",
        ):
            result = google_sync.pull_events(google_connection, db)

        assert result["events_created"] == 0


# ── Tests de Apple sync ───────────────────────────────────────────────────────

class TestAppleSync:

    def test_push_events_creates_apple_event(self, db, apple_connection, future_event):
        """push_events crea el evento en Apple y guarda el apple_event_id."""
        from app.modules.calendar_tracker.integrations.apple.sync import apple_sync

        mock_created     = MagicMock()
        mock_created.url = "https://caldav.icloud.com/calendar/new-uid-789.ics"

        with patch(
            "app.modules.calendar_tracker.integrations.apple.client.AppleCalendarClient.create_event",
            return_value=mock_created,
        ), patch(
            "app.modules.calendar_tracker.integrations.apple.client.AppleCalendarClient._get_calendar",
        ), patch(
            "app.modules.calendar_tracker.integrations.apple.auth.decrypt",
            return_value="decrypted-password",
        ):
            result = apple_sync.push_events(apple_connection, db)

        db.refresh(future_event)
        assert result["events_created"]  == 1
        assert future_event.apple_event_id == "new-uid-789"

    def test_pull_events_creates_local_event(self, db, apple_connection):
        """pull_events crea un evento local desde Apple."""
        from app.modules.calendar_tracker.integrations.apple.sync import apple_sync
        from app.modules.calendar_tracker.models.event import Event
        from app.core.auth.user import User

        user = db.query(User).filter(User.email == "test@test.com").first()

        mock_event      = MagicMock()
        mock_event.data = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "BEGIN:VEVENT\r\n"
            "UID:apple-pull-uid\r\n"
            "SUMMARY:Evento de Apple\r\n"
            "DTSTART:20260401T100000Z\r\n"
            "DTEND:20260401T110000Z\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )

        with patch(
            "app.modules.calendar_tracker.integrations.apple.client.AppleCalendarClient.list_events",
            return_value=[mock_event],
        ), patch(
            "app.modules.calendar_tracker.integrations.apple.client.AppleCalendarClient._get_calendar",
        ), patch(
            "app.modules.calendar_tracker.integrations.apple.auth.decrypt",
            return_value="decrypted-password",
        ):
            result = apple_sync.pull_events(apple_connection, db)

        assert result["events_created"] == 1
        event = db.query(Event).filter(
            Event.user_id        == user.id,
            Event.apple_event_id == "apple-pull-uid",
        ).first()
        assert event is not None
        assert event.title == "Evento de Apple"






# ── Test de integración real con Google ───────────────────────────────────────

import os

GOOGLE_TEST_REFRESH_TOKEN = os.getenv("GOOGLE_TEST_REFRESH_TOKEN")
GOOGLE_TEST_CALENDAR_ID   = os.getenv("GOOGLE_TEST_CALENDAR_ID", "primary")


@pytest.mark.skipif(
    not GOOGLE_TEST_REFRESH_TOKEN,
    reason="GOOGLE_TEST_REFRESH_TOKEN no configurado — test de integración real omitido"
)
class TestGoogleIntegration:

    def test_refresh_token_obtiene_access_token(self):
        """Verifica que el refresh_token funciona y obtenemos un access_token válido."""
        from app.modules.calendar_tracker.integrations.google.auth import refresh_access_token

        tokens = refresh_access_token(GOOGLE_TEST_REFRESH_TOKEN)
        assert tokens["access_token"] is not None
        assert tokens["expires_at"] is not None

    def test_list_calendars_real(self):
        from app.modules.calendar_tracker.integrations.google.auth import refresh_access_token
        from app.modules.calendar_tracker.integrations.google.client import GoogleCalendarClient
        from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection

        tokens     = refresh_access_token(GOOGLE_TEST_REFRESH_TOKEN)
        connection = CalendarConnection()
        connection.access_token     = tokens["access_token"]
        connection.refresh_token    = GOOGLE_TEST_REFRESH_TOKEN
        connection.token_expires_at = tokens["expires_at"]
        connection.calendar_id      = "primary"

        client    = GoogleCalendarClient(connection=connection, db=None)
        calendars = client.list_calendars()
        assert isinstance(calendars, list)
        assert len(calendars) > 0
        assert any(c.get("primary") is True for c in calendars)


    def test_create_and_delete_event_real(self):
        from datetime import datetime, timezone, timedelta
        from app.modules.calendar_tracker.integrations.google.auth import refresh_access_token
        from app.modules.calendar_tracker.integrations.google.client import GoogleCalendarClient
        from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection

        tokens     = refresh_access_token(GOOGLE_TEST_REFRESH_TOKEN)
        connection = CalendarConnection()
        connection.access_token     = tokens["access_token"]
        connection.refresh_token    = GOOGLE_TEST_REFRESH_TOKEN
        connection.token_expires_at = tokens["expires_at"]
        connection.calendar_id      = "primary"

        client = GoogleCalendarClient(connection=connection, db=None)
        now    = datetime.now(timezone.utc)
        body   = {
        "summary": "[TEST] Evento de integración — borrar",
        "start":   {"dateTime": (now + timedelta(hours=1)).isoformat(), "timeZone": "UTC"},
        "end":     {"dateTime": (now + timedelta(hours=2)).isoformat(), "timeZone": "UTC"},
    }
        created = client.create_event(body)
        assert created["id"] is not None
        assert created["summary"] == "[TEST] Evento de integración — borrar"
        client.delete_event(created["id"])


    def test_list_events_real(self):
        from datetime import datetime, timezone, timedelta
        from app.modules.calendar_tracker.integrations.google.auth import refresh_access_token
        from app.modules.calendar_tracker.integrations.google.client import GoogleCalendarClient
        from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection

        tokens     = refresh_access_token(GOOGLE_TEST_REFRESH_TOKEN)
        connection = CalendarConnection()
        connection.access_token     = tokens["access_token"]
        connection.refresh_token    = GOOGLE_TEST_REFRESH_TOKEN
        connection.token_expires_at = tokens["expires_at"]
        connection.calendar_id      = "primary"

        client = GoogleCalendarClient(connection=connection, db=None)
        now    = datetime.now(timezone.utc)
        events = client.list_events(
        time_min = now,
        time_max = now + timedelta(days=7),
    )
        assert isinstance(events, list)