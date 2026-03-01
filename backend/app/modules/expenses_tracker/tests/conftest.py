# app/modules/expenses_tracker/tests/conftest.py
import pytest


@pytest.fixture
def sample_expense_data():
    return {"name": "Test Expense", "quantity": 50.0, "account": "Imagin"}


@pytest.fixture
def expense_id(auth_client, sample_expense_data):
    response = auth_client.post("/api/v1/expenses/", json=sample_expense_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]