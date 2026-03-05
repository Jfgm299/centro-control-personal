# app/modules/expenses_tracker/tests/conftest.py
import pytest
from datetime import date, timedelta


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