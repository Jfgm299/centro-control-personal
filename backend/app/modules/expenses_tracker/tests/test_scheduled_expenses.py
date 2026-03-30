import pytest
from datetime import date, timedelta

# ── Helpers ───────────────────────────────────────────────────────────────────

BASE = "/api/v1/expenses/scheduled"

def subscription_payload(**overrides):
    data = {
        "name": "Netflix",
        "amount": 12.99,
        "account": "Revolut",
        "category": "SUBSCRIPTION",
        "frequency": "MONTHLY",
        "is_active": True,
    }
    data.update(overrides)
    return data

def one_time_payload(**overrides):
    data = {
        "name": "Hotel Roma",
        "amount": 150.0,
        "account": "Revolut",
        "category": "ONE_TIME",
        "frequency": "MONTHLY",  # ignorado para ONE_TIME
        "next_payment_date": str(date.today() + timedelta(days=10)),
        "is_active": True,
    }
    data.update(overrides)
    return data


@pytest.fixture
def subscription_id(auth_client):
    r = auth_client.post(BASE, json=subscription_payload())
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def one_time_id(auth_client):
    r = auth_client.post(BASE, json=one_time_payload())
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── Auth ──────────────────────────────────────────────────────────────────────

class TestScheduledAuth:

    def test_list_without_token_fails(self, client):
        assert client.get(BASE).status_code == 401

    def test_create_without_token_fails(self, client):
        assert client.post(BASE, json=subscription_payload()).status_code == 401

    def test_update_without_token_fails(self, client, auth_client, subscription_id):
        assert client.patch(f"{BASE}/{subscription_id}", json={"name": "X"}).status_code == 401

    def test_delete_without_token_fails(self, client, auth_client, subscription_id):
        assert client.delete(f"{BASE}/{subscription_id}").status_code == 401


# ── Ownership ─────────────────────────────────────────────────────────────────

class TestScheduledOwnership:

    def test_user_sees_only_own(self, auth_client, other_auth_client, subscription_id):
        other_auth_client.post(BASE, json=subscription_payload(name="Spotify"))
        r = auth_client.get(BASE)
        assert len(r.json()) == 1
        assert r.json()[0]["id"] == subscription_id

    def test_other_user_list_is_empty(self, auth_client, other_auth_client, subscription_id):
        r = other_auth_client.get(BASE)
        assert r.json() == []

    def test_cannot_update_other_users(self, auth_client, other_auth_client, subscription_id):
        r = other_auth_client.patch(f"{BASE}/{subscription_id}", json={"name": "Hack"})
        assert r.status_code == 404

    def test_cannot_delete_other_users(self, auth_client, other_auth_client, subscription_id):
        r = other_auth_client.delete(f"{BASE}/{subscription_id}")
        assert r.status_code == 404


# ── Create subscription ───────────────────────────────────────────────────────

class TestCreateSubscription:

    def test_create_subscription_success(self, auth_client):
        r = auth_client.post(BASE, json=subscription_payload())
        assert r.status_code == 201
        body = r.json()
        assert body["id"] is not None
        assert body["name"] == "Netflix"
        assert body["amount"] == 12.99
        assert body["category"] == "SUBSCRIPTION"
        assert body["frequency"] == "MONTHLY"
        assert body["is_active"] is True
        assert body["created_at"] is not None
        assert body["updated_at"] is None

    def test_create_subscription_weekly(self, auth_client):
        r = auth_client.post(BASE, json=subscription_payload(frequency="WEEKLY"))
        assert r.status_code == 201
        assert r.json()["frequency"] == "WEEKLY"

    def test_create_subscription_yearly(self, auth_client):
        r = auth_client.post(BASE, json=subscription_payload(frequency="YEARLY"))
        assert r.status_code == 201
        assert r.json()["frequency"] == "YEARLY"

    def test_create_subscription_imagin(self, auth_client):
        r = auth_client.post(BASE, json=subscription_payload(account="Imagin"))
        assert r.status_code == 201
        assert r.json()["account"] == "Imagin"

    def test_create_with_icon_and_notes(self, auth_client):
        r = auth_client.post(BASE, json=subscription_payload(icon="📺", notes="Plan familiar"))
        assert r.status_code == 201
        assert r.json()["icon"] == "📺"
        assert r.json()["notes"] == "Plan familiar"

    def test_create_with_next_payment_date(self, auth_client):
        future = str(date.today() + timedelta(days=5))
        r = auth_client.post(BASE, json=subscription_payload(next_payment_date=future))
        assert r.status_code == 201
        assert r.json()["next_payment_date"] == future

    def test_create_inactive_subscription(self, auth_client):
        r = auth_client.post(BASE, json=subscription_payload(is_active=False))
        assert r.status_code == 201
        assert r.json()["is_active"] is False

    def test_create_subscription_missing_name_fails(self, auth_client):
        data = subscription_payload()
        del data["name"]
        assert auth_client.post(BASE, json=data).status_code == 422

    def test_create_subscription_empty_name_fails(self, auth_client):
        assert auth_client.post(BASE, json=subscription_payload(name="")).status_code == 422

    def test_create_subscription_name_too_long_fails(self, auth_client):
        assert auth_client.post(BASE, json=subscription_payload(name="A" * 101)).status_code == 422

    def test_create_subscription_zero_amount_fails(self, auth_client):
        assert auth_client.post(BASE, json=subscription_payload(amount=0.0)).status_code == 422

    def test_create_subscription_negative_amount_fails(self, auth_client):
        assert auth_client.post(BASE, json=subscription_payload(amount=-5.0)).status_code == 422

    def test_create_subscription_invalid_account_fails(self, auth_client):
        assert auth_client.post(BASE, json=subscription_payload(account="PayPal")).status_code == 422

    def test_create_subscription_invalid_frequency_fails(self, auth_client):
        assert auth_client.post(BASE, json=subscription_payload(frequency="DAILY")).status_code == 422

    def test_create_subscription_invalid_category_fails(self, auth_client):
        assert auth_client.post(BASE, json=subscription_payload(category="UNKNOWN")).status_code == 422


# ── Create one_time ───────────────────────────────────────────────────────────

class TestCreateOneTime:

    def test_create_one_time_success(self, auth_client):
        r = auth_client.post(BASE, json=one_time_payload())
        assert r.status_code == 201
        body = r.json()
        assert body["category"] == "ONE_TIME"
        assert body["is_active"] is True

    def test_create_one_time_future_date(self, auth_client):
        future = str(date.today() + timedelta(days=30))
        r = auth_client.post(BASE, json=one_time_payload(next_payment_date=future))
        assert r.status_code == 201
        assert r.json()["next_payment_date"] == future

    def test_create_one_time_without_date(self, auth_client):
        data = one_time_payload()
        data["next_payment_date"] = None
        r = auth_client.post(BASE, json=data)
        assert r.status_code == 201
        assert r.json()["next_payment_date"] is None


# ── List ──────────────────────────────────────────────────────────────────────

class TestListScheduled:

    def test_list_empty(self, auth_client):
        r = auth_client.get(BASE)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_returns_created(self, auth_client, subscription_id):
        r = auth_client.get(BASE)
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["id"] == subscription_id

    def test_list_multiple(self, auth_client):
        auth_client.post(BASE, json=subscription_payload(name="Netflix"))
        auth_client.post(BASE, json=subscription_payload(name="Spotify"))
        auth_client.post(BASE, json=one_time_payload(name="Hotel"))
        r = auth_client.get(BASE)
        assert len(r.json()) == 3

    def test_list_response_fields(self, auth_client, subscription_id):
        item = auth_client.get(BASE).json()[0]
        for field in ["id", "name", "amount", "account", "category", "frequency",
                      "is_active", "created_at", "updated_at"]:
            assert field in item

    def test_list_ordered_by_next_payment_date(self, auth_client):
        auth_client.post(BASE, json=subscription_payload(
            name="Far", next_payment_date=str(date.today() + timedelta(days=30))))
        auth_client.post(BASE, json=subscription_payload(
            name="Near", next_payment_date=str(date.today() + timedelta(days=5))))
        r = auth_client.get(BASE)
        names = [i["name"] for i in r.json() if i["next_payment_date"]]
        assert names[0] == "Near"


# ── Update ────────────────────────────────────────────────────────────────────

class TestUpdateScheduled:

    def test_update_name(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"name": "Disney+"})
        assert r.status_code == 200
        assert r.json()["name"] == "Disney+"

    def test_update_amount(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"amount": 19.99})
        assert r.status_code == 200
        assert r.json()["amount"] == 19.99

    def test_update_frequency(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"frequency": "YEARLY"})
        assert r.status_code == 200
        assert r.json()["frequency"] == "YEARLY"

    def test_update_is_active_false(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"is_active": False})
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_update_sets_updated_at(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"name": "Updated"})
        assert r.json()["updated_at"] is not None

    def test_partial_update_preserves_other_fields(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"amount": 5.0})
        body = r.json()
        assert body["name"] == "Netflix"
        assert body["category"] == "SUBSCRIPTION"

    def test_update_not_found(self, auth_client):
        r = auth_client.patch(f"{BASE}/99999", json={"name": "X"})
        assert r.status_code == 404

    def test_update_zero_amount_fails(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"amount": 0.0})
        assert r.status_code == 422

    def test_update_negative_amount_fails(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"amount": -1.0})
        assert r.status_code == 422

    def test_update_empty_name_fails(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"name": ""})
        assert r.status_code == 422

    def test_update_invalid_account_fails(self, auth_client, subscription_id):
        r = auth_client.patch(f"{BASE}/{subscription_id}", json={"account": "Bizum"})
        assert r.status_code == 422


# ── Delete ────────────────────────────────────────────────────────────────────

class TestDeleteScheduled:

    def test_delete_success(self, auth_client, subscription_id):
        r = auth_client.delete(f"{BASE}/{subscription_id}")
        assert r.status_code == 204

    def test_delete_removes_from_list(self, auth_client, subscription_id):
        auth_client.delete(f"{BASE}/{subscription_id}")
        assert auth_client.get(BASE).json() == []

    def test_delete_not_found(self, auth_client):
        assert auth_client.delete(f"{BASE}/99999").status_code == 404

    def test_delete_twice_fails(self, auth_client, subscription_id):
        auth_client.delete(f"{BASE}/{subscription_id}")
        assert auth_client.delete(f"{BASE}/{subscription_id}").status_code == 404

    def test_delete_preserves_others(self, auth_client):
        r1 = auth_client.post(BASE, json=subscription_payload(name="A"))
        r2 = auth_client.post(BASE, json=subscription_payload(name="B"))
        auth_client.delete(f"{BASE}/{r1.json()['id']}")
        remaining = auth_client.get(BASE).json()
        assert len(remaining) == 1
        assert remaining[0]["id"] == r2.json()["id"]


# ── Auto-convert ONE_TIME past date ──────────────────────────────────────────

class TestAutoConvert:

    def test_past_one_time_converts_to_expense(self, auth_client):
        """Un ONE_TIME con fecha pasada debe crear un Expense real al hacer GET."""
        yesterday = str(date.today() - timedelta(days=1))
        r = auth_client.post(BASE, json=one_time_payload(
            name="Vuelo Madrid",
            amount=89.0,
            next_payment_date=yesterday,
        ))
        assert r.status_code == 201

        # Al listar, el servicio detecta la fecha pasada y convierte
        auth_client.get(BASE)

        # Debe aparecer en gastos reales
        expenses = auth_client.get("/api/v1/expenses/").json()
        converted = [e for e in expenses if e["name"] == "Vuelo Madrid"]
        assert len(converted) == 1
        assert converted[0]["quantity"] == 89.0

    def test_past_one_time_becomes_inactive(self, auth_client):
        """El ONE_TIME convertido debe desaparecer de la lista (is_active=False → filtrado)."""
        yesterday = str(date.today() - timedelta(days=1))
        r = auth_client.post(BASE, json=one_time_payload(
            name="Hotel Paris",
            next_payment_date=yesterday,
        ))
        item_id = r.json()["id"]

        auth_client.get(BASE)  # trigger auto-convert

        scheduled = auth_client.get(BASE).json()
        ids = [s["id"] for s in scheduled]
        assert item_id not in ids

    def test_past_one_time_not_converted_twice(self, auth_client):
        """Llamar GET dos veces no debe crear dos Expenses."""
        yesterday = str(date.today() - timedelta(days=1))
        auth_client.post(BASE, json=one_time_payload(
            name="Concierto",
            amount=45.0,
            next_payment_date=yesterday,
        ))

        auth_client.get(BASE)
        auth_client.get(BASE)

        expenses = auth_client.get("/api/v1/expenses/").json()
        converted = [e for e in expenses if e["name"] == "Concierto"]
        assert len(converted) == 1

    def test_future_one_time_not_converted(self, auth_client):
        """Un ONE_TIME con fecha futura NO debe convertirse."""
        future = str(date.today() + timedelta(days=10))
        auth_client.post(BASE, json=one_time_payload(
            name="Reserva Hotel",
            next_payment_date=future,
        ))

        auth_client.get(BASE)

        expenses = auth_client.get("/api/v1/expenses/").json()
        converted = [e for e in expenses if e["name"] == "Reserva Hotel"]
        assert len(converted) == 0

    def test_today_one_time_converts(self, auth_client):
        """Un ONE_TIME con fecha de hoy debe convertirse."""
        today = str(date.today())
        auth_client.post(BASE, json=one_time_payload(
            name="Pago hoy",
            amount=30.0,
            next_payment_date=today,
        ))

        auth_client.get(BASE)

        expenses = auth_client.get("/api/v1/expenses/").json()
        converted = [e for e in expenses if e["name"] == "Pago hoy"]
        assert len(converted) == 1

    def test_subscription_past_date_is_converted_and_advanced(self, auth_client):
        """Una SUBSCRIPTION con fecha pasada debe convertirse en Expense y avanzar su fecha."""
        from dateutil.relativedelta import relativedelta
        yesterday = str(date.today() - timedelta(days=1))
        
        r = auth_client.post(BASE, json=subscription_payload(
            name="Netflix recurrente",
            next_payment_date=yesterday,
            frequency="MONTHLY"
        ))
        sub_id = r.json()["id"]

        # Trigger conversion
        auth_client.get(BASE)

        # Check expense was created
        expenses = auth_client.get("/api/v1/expenses/").json()
        converted = [e for e in expenses if e["name"] == "Netflix recurrente"]
        assert len(converted) == 1
        
        # Check subscription date was advanced
        subs = auth_client.get(BASE).json()
        updated_sub = [s for s in subs if s["id"] == sub_id][0]
        expected_next = date.today() - timedelta(days=1) + relativedelta(months=1)
        assert updated_sub["next_payment_date"] == str(expected_next)
        assert updated_sub["is_active"] is True

    def test_inactive_one_time_not_converted(self, auth_client):
        """Un ONE_TIME inactivo con fecha pasada NO debe convertirse."""
        yesterday = str(date.today() - timedelta(days=1))
        auth_client.post(BASE, json=one_time_payload(
            name="Cancelado",
            next_payment_date=yesterday,
            is_active=False,
        ))

        auth_client.get(BASE)

        expenses = auth_client.get("/api/v1/expenses/").json()
        converted = [e for e in expenses if e["name"] == "Cancelado"]
        assert len(converted) == 0

    def test_converted_expense_has_correct_account(self, auth_client):
        """El Expense creado debe tener la misma cuenta que el ONE_TIME."""
        yesterday = str(date.today() - timedelta(days=1))
        auth_client.post(BASE, json=one_time_payload(
            name="Pago Imagin",
            account="Imagin",
            next_payment_date=yesterday,
        ))

        auth_client.get(BASE)

        expenses = auth_client.get("/api/v1/expenses/").json()
        converted = [e for e in expenses if e["name"] == "Pago Imagin"]
        assert converted[0]["account"] == "Imagin"