# app/modules/expenses_tracker/tests/conftest.py
import pytest
from datetime import date, timedelta


@pytest.fixture(autouse=True)
def clear_expenses_dispatch_cache():
    """Limpia los caches de deduplicación del scheduler entre tests."""
    from app.modules.expenses_tracker import scheduler_service
    scheduler_service._subscription_due_cache.clear()
    scheduler_service._budget_exceeded_cache.clear()
    yield
    scheduler_service._subscription_due_cache.clear()
    scheduler_service._budget_exceeded_cache.clear()


# ── Fixtures existentes ───────────────────────────────────────────────────────

@pytest.fixture
def sample_expense_data():
    return {"name": "Test Expense", "quantity": 50.0, "account": "Imagin"}


@pytest.fixture
def expense_id(auth_client, sample_expense_data):
    response = auth_client.post("/api/v1/expenses/", json=sample_expense_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def subscription_id(auth_client):
    r = auth_client.post("/api/v1/expenses/scheduled", json={
        "name": "Netflix",
        "amount": 12.99,
        "account": "Revolut",
        "category": "SUBSCRIPTION",
        "frequency": "MONTHLY",
        "is_active": True,
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def one_time_id(auth_client):
    r = auth_client.post("/api/v1/expenses/scheduled", json={
        "name": "Hotel Roma",
        "amount": 150.0,
        "account": "Revolut",
        "category": "ONE_TIME",
        "frequency": "MONTHLY",
        "next_payment_date": str(date.today() + timedelta(days=10)),
        "is_active": True,
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── Nuevas fixtures para automation contract ──────────────────────────────────

@pytest.fixture
def expense_data():
    return {"name": "Gasto test", "quantity": 200.0, "account": "Revolut"}


@pytest.fixture
def large_expense_id(auth_client, expense_data):
    """Gasto por encima del umbral (200€ > 100€ por defecto)."""
    response = auth_client.post("/api/v1/expenses/", json=expense_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def small_expense_id(auth_client):
    """Gasto por debajo del umbral (10€)."""
    response = auth_client.post("/api/v1/expenses/", json={
        "name": "Café",
        "quantity": 10.0,
        "account": "Imagin",
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def scheduled_expense_data():
    return {
        "name":      "Spotify",
        "amount":    9.99,
        "account":   "Revolut",
        "category":  "SUBSCRIPTION",
        "frequency": "MONTHLY",
        "is_active": True,
    }


@pytest.fixture
def scheduled_expense_id(auth_client, scheduled_expense_data):
    r = auth_client.post("/api/v1/expenses/scheduled", json=scheduled_expense_data)
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def overdue_subscription_id(auth_client):
    """Suscripción con next_payment_date en el pasado (vencida)."""
    r = auth_client.post("/api/v1/expenses/scheduled", json={
        "name":              "Suscripción vencida",
        "amount":            15.0,
        "account":           "Revolut",
        "category":          "SUBSCRIPTION",
        "frequency":         "MONTHLY",
        "next_payment_date": str(date.today() - timedelta(days=5)),
        "is_active":         True,
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def upcoming_subscription_id(auth_client):
    """Suscripción con next_payment_date en 3 días."""
    r = auth_client.post("/api/v1/expenses/scheduled", json={
        "name":              "Suscripción próxima",
        "amount":            9.99,
        "account":           "Imagin",
        "category":          "SUBSCRIPTION",
        "frequency":         "MONTHLY",
        "next_payment_date": str(date.today() + timedelta(days=3)),
        "is_active":         True,
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── Fixtures de automatizaciones ──────────────────────────────────────────────

@pytest.fixture(autouse=True, scope="session")
def register_expenses_triggers():
    """Registra los triggers y acciones de expenses_tracker en el registry."""
    from app.modules.automations_engine.core.registry import registry

    registry.register_trigger(
        module_id="expenses_tracker",
        trigger_id="large_expense_created",
        label="Gasto grande creado",
        config_schema={},
        handler="app.modules.expenses_tracker.automation_handlers.handle_large_expense_created",
    )
    registry.register_trigger(
        module_id="expenses_tracker",
        trigger_id="monthly_budget_exceeded",
        label="Presupuesto mensual superado",
        config_schema={},
        handler="app.modules.expenses_tracker.automation_handlers.handle_monthly_budget_exceeded",
    )
    registry.register_trigger(
        module_id="expenses_tracker",
        trigger_id="subscription_due_soon",
        label="Suscripción próxima a vencer",
        config_schema={},
        handler="app.modules.expenses_tracker.automation_handlers.handle_subscription_due_soon",
    )
    registry.register_trigger(
        module_id="expenses_tracker",
        trigger_id="subscription_converted",
        label="Suscripción convertida en gasto",
        config_schema={},
        handler="app.modules.expenses_tracker.automation_handlers.handle_subscription_converted",
    )
    registry.register_action(
        module_id="expenses_tracker",
        action_id="create_expense",
        label="Crear gasto puntual",
        config_schema={},
        handler="app.modules.expenses_tracker.automation_handlers.action_create_expense",
    )
    registry.register_action(
        module_id="expenses_tracker",
        action_id="get_monthly_summary",
        label="Resumen mensual",
        config_schema={},
        handler="app.modules.expenses_tracker.automation_handlers.action_get_monthly_summary",
    )
    registry.register_action(
        module_id="expenses_tracker",
        action_id="get_upcoming_subscriptions",
        label="Suscripciones próximas",
        config_schema={},
        handler="app.modules.expenses_tracker.automation_handlers.action_get_upcoming_subscriptions",
    )
    yield


@pytest.fixture
def automation_for_large_expense(auth_client):
    """Automatización suscrita a expenses_tracker.large_expense_created."""
    r = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto large expense",
        "trigger_type": "module_event",
        "trigger_ref":  "expenses_tracker.large_expense_created",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "expenses_tracker.large_expense_created", "min_amount": 100.0}},
                {"id": "n2", "type": "action",  "config": {"action_id": "expenses_tracker.get_monthly_summary"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        },
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def automation_for_subscription_converted(auth_client):
    """Automatización suscrita a expenses_tracker.subscription_converted."""
    r = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto subscription converted",
        "trigger_type": "module_event",
        "trigger_ref":  "expenses_tracker.subscription_converted",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "expenses_tracker.subscription_converted"}},
                {"id": "n2", "type": "action",  "config": {"action_id": "expenses_tracker.get_monthly_summary"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        },
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def automation_for_subscription_due_soon(auth_client):
    """Automatización suscrita a expenses_tracker.subscription_due_soon."""
    r = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto subscription due soon",
        "trigger_type": "module_event",
        "trigger_ref":  "expenses_tracker.subscription_due_soon",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "expenses_tracker.subscription_due_soon", "days_ahead": 7}},
                {"id": "n2", "type": "action",  "config": {"action_id": "expenses_tracker.get_upcoming_subscriptions"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        },
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]
