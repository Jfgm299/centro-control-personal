import pytest
from unittest.mock import patch, AsyncMock
from datetime import date, timedelta

from app.modules.macro_tracker.exceptions import (
    ProductNotFoundInAPIError,
    OFFTimeoutError,
    OFFRateLimitError,
)

MOCK_PRODUCT_RAW = {
    "code": "8480000342591",
    "product_name": "Arroz redondo",
    "brands": "Hacendado",
    "serving_size": "100g",
    "serving_quantity": 100.0,
    "nutrition_grades": "b",
    "image_front_small_url": "https://images.openfoodfacts.org/arroz.jpg",
    "categories_tags": ["en:cereals", "en:rices"],
    "allergens_tags": [],
    "nutriments": {
        "energy-kcal_100g": 354.0,
        "proteins_100g": 7.0,
        "carbohydrates_100g": 77.0,
        "sugars_100g": 0.4,
        "fat_100g": 0.9,
        "saturated-fat_100g": 0.2,
        "fiber_100g": 0.6,
        "salt_100g": 0.01,
        "sodium_100g": 0.004,
    },
}

MOCK_PRODUCT_PARTIAL_RAW = {
    "code": "1234567890123",
    "product_name": "Producto incompleto",
    "brands": "MarcaX",
    "nutriments": {"energy-kcal_100g": 200.0},
}


@pytest.fixture
def mock_off_client():
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock, return_value=MOCK_PRODUCT_RAW,
    ):
        yield

@pytest.fixture
def mock_off_not_found():
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock, side_effect=ProductNotFoundInAPIError("0000000000000"),
    ):
        yield

@pytest.fixture
def mock_off_timeout():
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock, side_effect=OFFTimeoutError(),
    ):
        yield

@pytest.fixture
def mock_off_rate_limit():
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock, side_effect=OFFRateLimitError(),
    ):
        yield

@pytest.fixture
def mock_off_partial():
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock, return_value=MOCK_PRODUCT_PARTIAL_RAW,
    ):
        yield

@pytest.fixture
def sample_barcode():
    return "8480000342591"

@pytest.fixture
def sample_diary_entry_data():
    return {"entry_date": date.today().isoformat(), "meal_type": "lunch", "amount_g": 150.0}

@pytest.fixture
def cached_product_id(auth_client, mock_off_client, sample_barcode):
    response = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
    assert response.status_code == 200, response.json()
    return response.json()["id"]

@pytest.fixture
def partial_product_id(auth_client, mock_off_partial):
    response = auth_client.get("/api/v1/macros/products/barcode/1234567890123")
    assert response.status_code == 200, response.json()
    return response.json()["id"]

@pytest.fixture
def diary_entry_id(auth_client, cached_product_id, sample_diary_entry_data):
    data = {**sample_diary_entry_data, "product_id": cached_product_id}
    response = auth_client.post("/api/v1/macros/diary", json=data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]

@pytest.fixture
def multiple_diary_entries(auth_client, mock_off_client, sample_barcode):
    product_resp = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
    product_id = product_resp.json()["id"]
    ids = []
    meal_types = ["breakfast", "lunch", "dinner", "morning_snack", "afternoon_snack",
                "breakfast", "lunch", "dinner", "breakfast", "lunch"]
    for i, meal in enumerate(meal_types):
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": product_id,
            "entry_date": (date.today() - timedelta(days=i % 5)).isoformat(),
            "meal_type": meal,
            "amount_g": 100.0 + i * 10,
        })
        assert resp.status_code == 201, resp.json()
        ids.append(resp.json()["id"])
    return ids

@pytest.fixture
def user_goal_id(auth_client):
    response = auth_client.get("/api/v1/macros/goals")
    assert response.status_code == 200, response.json()
    return response.json()["id"]