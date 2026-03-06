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
    now   = datetime.now(timezone.utc)
    start = now + timedelta(minutes=30)
    # Si pasamos de las 23:00 UTC, usamos el inicio del día siguiente
    # para que start < end y ambos sean coherentes
    end   = start + timedelta(hours=1)
    return {
        "title":    "Clase de algebra",
        "start_at": start.isoformat(),
        "end_at":   end.isoformat(),
    }


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


# ── Fixtures para dispatcher de automatizaciones ──────────────────────────────

@pytest.fixture(autouse=True, scope="session")
def register_calendar_triggers():
    """Registra los triggers reales de calendar_tracker en el registry."""
    from app.modules.automations_engine.core.registry import registry
    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="event_start",
        label="Al iniciar un evento",
        config_schema={},
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_event_start",
    )
    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="event_end",
        label="Al finalizar un evento",
        config_schema={},
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_event_end",
    )
    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="reminder_due",
        label="Cuando vence un recordatorio",
        config_schema={},
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_reminder_due",
    )
    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="no_events_in_window",
        label="Cuando hay tiempo libre",
        config_schema={},
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_no_events_in_window",
    )
    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="overdue_reminders_exist",
        label="Cuando hay recordatorios vencidos",
        config_schema={},
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_overdue_reminders_exist",
    )
    registry.register_action(
        module_id="calendar_tracker",
        action_id="push_summary_overdue",
        label="Resumen de vencidos",
        config_schema={},
        handler="app.modules.calendar_tracker.services.automation_handlers.action_push_summary_overdue",
    )
    registry.register_action(
        module_id="calendar_tracker",
        action_id="get_todays_schedule",
        label="Eventos de hoy",
        config_schema={},
        handler="app.modules.calendar_tracker.services.automation_handlers.action_get_todays_schedule",
    )
    yield


@pytest.fixture
def event_starting_now(auth_client):
    """Evento que empieza ahora mismo — dentro de la ventana del scheduler."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    data = {
        "title":    "Evento ahora",
        "start_at": (now - timedelta(seconds=30)).isoformat(),
        "end_at":   (now + timedelta(hours=1)).isoformat(),
    }
    response = auth_client.post("/api/v1/calendar/events", json=data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def event_ending_now(auth_client):
    """Evento que termina ahora mismo — dentro de la ventana del scheduler."""
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    data = {
        "title":    "Evento terminando",
        "start_at": (now - timedelta(hours=1)).isoformat(),
        "end_at":   (now - timedelta(seconds=30)).isoformat(),
    }
    response = auth_client.post("/api/v1/calendar/events", json=data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def overdue_reminder_id(auth_client):
    """Recordatorio con due_date en el pasado — vencido."""
    from datetime import date, timedelta
    response = auth_client.post("/api/v1/calendar/reminders", json={
        "title":    "Recordatorio vencido",
        "priority": "high",
        "due_date": (date.today() - timedelta(days=3)).isoformat(),
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def reminder_due_today_id(auth_client):
    """Recordatorio con due_date hoy."""
    from datetime import date
    response = auth_client.post("/api/v1/calendar/reminders", json={
        "title":    "Recordatorio hoy",
        "priority": "high",
        "due_date": date.today().isoformat(),
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def automation_for_event_start(auth_client):
    """Automatización suscrita a calendar_tracker.event_start."""
    response = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto event start",
        "trigger_type": "module_event",
        "trigger_ref":  "calendar_tracker.event_start",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "calendar_tracker.event_start"}},
                {"id": "n2", "type": "action",  "config": {"action_id": "calendar_tracker.get_todays_schedule"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}]
        }
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def automation_for_event_end(auth_client):
    """Automatización suscrita a calendar_tracker.event_end."""
    response = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto event end",
        "trigger_type": "module_event",
        "trigger_ref":  "calendar_tracker.event_end",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "calendar_tracker.event_end"}},
                {"id": "n2", "type": "action",  "config": {"action_id": "calendar_tracker.get_todays_schedule"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}]
        }
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def automation_for_reminder_due(auth_client):
    """Automatización suscrita a calendar_tracker.reminder_due."""
    response = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto reminder due",
        "trigger_type": "module_event",
        "trigger_ref":  "calendar_tracker.reminder_due",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "calendar_tracker.reminder_due"}},
                {"id": "n2", "type": "action",  "config": {"action_id": "calendar_tracker.push_summary_overdue"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}]
        }
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def automation_for_overdue(auth_client):
    """Automatización suscrita a calendar_tracker.overdue_reminders_exist."""
    response = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto overdue",
        "trigger_type": "module_event",
        "trigger_ref":  "calendar_tracker.overdue_reminders_exist",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "calendar_tracker.overdue_reminders_exist"}},
                {"id": "n2", "type": "action",  "config": {"action_id": "calendar_tracker.push_summary_overdue"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}]
        }
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]

@pytest.fixture
def automation_for_free_window(auth_client):
    """Automatización suscrita a calendar_tracker.no_events_in_window."""
    response = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto free window",
        "trigger_type": "module_event",
        "trigger_ref":  "calendar_tracker.no_events_in_window",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "calendar_tracker.no_events_in_window"}},
                {"id": "n2", "type": "action",  "config": {"action_id": "calendar_tracker.get_todays_schedule"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}]
        }
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]