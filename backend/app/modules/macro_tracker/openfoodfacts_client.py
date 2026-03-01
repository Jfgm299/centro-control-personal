import httpx
from app.core.config import settings
from .exceptions import ProductNotFoundInAPIError, OFFTimeoutError, OFFRateLimitError, OFFError


class OpenFoodFactsClient:
    BASE_URL = settings.OFF_BASE_URL
    FIELDS = (
        "code,product_name,brands,serving_size,serving_quantity,"
        "nutriments,nutrition_grades,image_front_small_url,"
        "categories_tags,allergens_tags"
    )
    TIMEOUT = 10.0
    # OFF requiere User-Agent identificativo — política de uso
    USER_AGENT = "CentroControl/1.0 (contacto@centrocontrol.app)"

    async def get_product(self, barcode: str) -> dict:
        """GET /api/v2/product/{barcode} — 1 llamada, devuelve el dict 'product'"""
        url = f"{self.BASE_URL}/api/v2/product/{barcode}"
        params = {"fields": self.FIELDS}
        headers = {"User-Agent": self.USER_AGENT}

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                raise OFFRateLimitError()

            response.raise_for_status()
            data = response.json()

            if data.get("status") == 0:
                raise ProductNotFoundInAPIError(barcode)

            return data.get("product", {})

        except httpx.TimeoutException:
            raise OFFTimeoutError()
        except (OFFRateLimitError, OFFTimeoutError, ProductNotFoundInAPIError):
            raise
        except httpx.HTTPStatusError:
            raise OFFError()

    async def search_by_name(self, query: str, page_size: int = 10) -> list[dict]:
        """GET /api/v2/search — búsqueda por nombre, devuelve lista de dicts 'product'"""
        url = f"{self.BASE_URL}/api/v2/search"
        params = {
            "search_terms": query,
            "fields": self.FIELDS,
            "page_size": page_size,
            "sort_by": "popularity_key",
        }
        headers = {"User-Agent": self.USER_AGENT}

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("products", [])
        except httpx.TimeoutException:
            raise OFFTimeoutError()
        except httpx.HTTPStatusError:
            raise OFFError()

    def parse_product(self, raw: dict) -> dict:
        """Normaliza el dict 'product' de OFF a los campos de la tabla products."""
        nutriments = raw.get("nutriments", {})
        brands_raw = raw.get("brands") or ""
        # OFF a veces devuelve varias marcas separadas por coma — tomamos la primera
        brand = brands_raw.split(",")[0].strip() or None

        return {
            "barcode":            raw.get("code"),
            "product_name":       raw.get("product_name") or "Producto sin nombre",
            "brand":              brand,
            "serving_size_text":  raw.get("serving_size"),
            "serving_quantity_g": raw.get("serving_quantity"),
            "nutriscore":         raw.get("nutrition_grades"),
            "image_url":          raw.get("image_front_small_url"),
            "categories":         ",".join(raw.get("categories_tags") or [])[:500] or None,
            "allergens":          ",".join(raw.get("allergens_tags") or [])[:300] or None,
            "energy_kcal_100g":   self._get_nutriment(nutriments, "energy-kcal"),
            "proteins_100g":      self._get_nutriment(nutriments, "proteins"),
            "carbohydrates_100g": self._get_nutriment(nutriments, "carbohydrates"),
            "sugars_100g":        self._get_nutriment(nutriments, "sugars"),
            "fat_100g":           self._get_nutriment(nutriments, "fat"),
            "saturated_fat_100g": self._get_nutriment(nutriments, "saturated-fat"),
            "fiber_100g":         self._get_nutriment(nutriments, "fiber"),
            "salt_100g":          self._get_nutriment(nutriments, "salt"),
            "sodium_100g":        self._get_nutriment(nutriments, "sodium"),
            "source":             "openfoodfacts",
            "off_raw_data":       raw,
        }

    def _get_nutriment(self, nutriments: dict, key: str) -> float | None:
        """Busca primero la clave _100g, luego la clave base. Defensivo ante tipos inesperados."""
        value = nutriments.get(f"{key}_100g")
        if value is None:
            value = nutriments.get(key)
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None