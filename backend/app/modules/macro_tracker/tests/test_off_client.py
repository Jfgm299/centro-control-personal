import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.modules.macro_tracker.openfoodfacts_client import OpenFoodFactsClient
from app.modules.macro_tracker.exceptions import (
    ProductNotFoundInAPIError,
    OFFTimeoutError,
    OFFRateLimitError,
    OFFError,
)

# Definir los mocks aquí directamente — sin importar desde backend.conftest
MOCK_PRODUCT = {
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

MOCK_PRODUCT_PARTIAL = {
    "code": "1234567890123",
    "product_name": "Producto incompleto",
    "brands": "MarcaX",
    "nutriments": {
        "energy-kcal_100g": 200.0,
    },
}


def make_mock_response(status_code: int, json_data: dict):
    """Construye un mock de respuesta httpx compatible con async context manager."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.raise_for_status = MagicMock()
    return mock_response


def patch_httpx_get(mock_response):
    """
    Parchea httpx.AsyncClient para que funcione como async context manager.
    El cliente se usa como: async with httpx.AsyncClient() as client: response = await client.get(...)
    """
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)

    mock_client_class = MagicMock()
    mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

    return patch("app.modules.macro_tracker.openfoodfacts_client.httpx.AsyncClient", mock_client_class)


@pytest.fixture
def off_client():
    return OpenFoodFactsClient()


class TestParseProduct:
    """Tests unitarios de parse_product — sin red, sin BD"""

    def test_parse_complete_product(self, off_client):
        parsed = off_client.parse_product(MOCK_PRODUCT)
        assert parsed["barcode"]           == "8480000342591"
        assert parsed["product_name"]      == "Arroz redondo"
        assert parsed["brand"]             == "Hacendado"
        assert parsed["energy_kcal_100g"]  == 354.0
        assert parsed["proteins_100g"]     == 7.0
        assert parsed["source"]            == "openfoodfacts"

    def test_parse_partial_product_nulls(self, off_client):
        parsed = off_client.parse_product(MOCK_PRODUCT_PARTIAL)
        assert parsed["energy_kcal_100g"] == 200.0
        assert parsed["proteins_100g"]    is None
        assert parsed["fat_100g"]         is None

    def test_parse_missing_product_name(self, off_client):
        parsed = off_client.parse_product({"nutriments": {}})
        assert parsed["product_name"] == "Producto sin nombre"

    def test_parse_multiple_brands_takes_first(self, off_client):
        raw = {"product_name": "Test", "brands": "Marca A, Marca B", "nutriments": {}}
        parsed = off_client.parse_product(raw)
        assert parsed["brand"] == "Marca A"

    def test_parse_empty_nutriments(self, off_client):
        parsed = off_client.parse_product({"product_name": "Test", "nutriments": {}})
        for field in ["energy_kcal_100g", "proteins_100g", "fat_100g", "fiber_100g"]:
            assert parsed[field] is None

    def test_get_nutriment_prefers_100g_key(self, off_client):
        nutriments = {"proteins_100g": 10.0, "proteins": 8.0}
        assert off_client._get_nutriment(nutriments, "proteins") == 10.0

    def test_get_nutriment_fallback_to_base_key(self, off_client):
        nutriments = {"proteins": 8.0}
        assert off_client._get_nutriment(nutriments, "proteins") == 8.0

    def test_get_nutriment_invalid_type_returns_none(self, off_client):
        nutriments = {"proteins_100g": "no-es-numero"}
        assert off_client._get_nutriment(nutriments, "proteins") is None


class TestGetProduct:

    @pytest.mark.asyncio
    async def test_get_product_success(self, off_client):
        mock_response = make_mock_response(200, {"status": 1, "product": MOCK_PRODUCT})
        with patch_httpx_get(mock_response):
            result = await off_client.get_product("8480000342591")
        assert result["product_name"] == "Arroz redondo"

    @pytest.mark.asyncio
    async def test_get_product_status_0_raises(self, off_client):
        mock_response = make_mock_response(200, {"status": 0})
        with patch_httpx_get(mock_response):
            with pytest.raises(ProductNotFoundInAPIError):
                await off_client.get_product("0000000000000")

    @pytest.mark.asyncio
    async def test_get_product_timeout_raises(self, off_client):
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )
        mock_client_class = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("app.modules.macro_tracker.openfoodfacts_client.httpx.AsyncClient", mock_client_class):
            with pytest.raises(OFFTimeoutError):
                await off_client.get_product("8480000342591")

    @pytest.mark.asyncio
    async def test_get_product_429_raises_rate_limit(self, off_client):
        mock_response = make_mock_response(429, {})
        mock_response.raise_for_status = MagicMock()
        with patch_httpx_get(mock_response):
            with pytest.raises(OFFRateLimitError):
                await off_client.get_product("8480000342591")