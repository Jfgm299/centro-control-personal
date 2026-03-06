import pytest
from datetime import datetime, timezone, timedelta


# ── Fixtures de categorías ────────────────────────────────────────────────────

@pytest.fixture
def category_data():
    return {"name": "Universidad", "icon": "🎓"}


@pytest.fixture
def category_id(auth_client, category_data):
    response = auth_client.post("/api/v1/calendar/categories", json=category_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def second_category_id(auth_client):
    response = auth_client.post("/api/v1/calendar/categories", json={"name": "Gimnasio", "icon": "💪"})
    assert response.status_code == 201, response.json()
    return response.json()["id"]


# ── Fixtures de recordatorios ─────────────────────────────────────────────────

@pytest.fixture
def reminder_data():
    return {"title": "Comprar leche", "priority": "medium"}


@pytest.fixture
def reminder_id(auth_client, reminder_data):
    response = auth_client.post("/api/v1/calendar/reminders", json=reminder_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def urgent_reminder_id(auth_client):
    response = auth_client.post("/api/v1/calendar/reminders", json={
        "title": "Entregar trabajo URGENTE",
        "priority": "urgent",
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


# ── Fixtures de eventos ───────────────────────────────────────────────────────

def _future_range(offset_hours: int = 2, duration_hours: int = 1) -> dict:
    """Devuelve start_at y end_at en el futuro como strings ISO 8601."""
    start = datetime.now(timezone.utc) + timedelta(hours=offset_hours)
    end   = start + timedelta(hours=duration_hours)
    return {
        "start_at": start.isoformat(),
        "end_at":   end.isoformat(),
    }


@pytest.fixture
def event_data():
    return {"title": "Clase de algebra", **_future_range()}


@pytest.fixture
def event_id(auth_client, event_data):
    response = auth_client.post("/api/v1/calendar/events", json=event_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def event_with_reminder_id(auth_client):
    data = {"title": "Reunion importante", "reminder_minutes": 15, **_future_range(offset_hours=3)}
    response = auth_client.post("/api/v1/calendar/events", json=data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def event_with_dnd_id(auth_client):
    data = {"title": "Examen final", "enable_dnd": True, **_future_range(offset_hours=4)}
    response = auth_client.post("/api/v1/calendar/events", json=data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def scheduled_reminder(auth_client, reminder_id):
    """Reminder ya asignado a una franja — devuelve (reminder_id, event_id)."""
    times = _future_range(offset_hours=5)
    response = auth_client.post(f"/api/v1/calendar/reminders/{reminder_id}/schedule", json=times)
    assert response.status_code == 201, response.json()
    return reminder_id, response.json()["id"]


# ── Fixtures de rutinas ───────────────────────────────────────────────────────

@pytest.fixture
def routine_data():
    return {
        "title":      "Gym - Hombros",
        "rrule":      "FREQ=WEEKLY;BYDAY=MO",
        "start_time": "18:00:00",
        "end_time":   "20:00:00",
        "valid_from": "2026-01-01",
    }


@pytest.fixture
def routine_id(auth_client, routine_data):
    response = auth_client.post("/api/v1/calendar/routines", json=routine_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]