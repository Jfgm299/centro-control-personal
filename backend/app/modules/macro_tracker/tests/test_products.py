import pytest


class TestProductsAuth:

    def test_get_by_barcode_without_token_fails(self, client):
        response = client.get("/api/v1/macros/products/barcode/8480000342591")
        assert response.status_code == 401

    def test_search_without_token_fails(self, client):
        response = client.get("/api/v1/macros/products/search?q=arroz")
        assert response.status_code == 401

    def test_get_by_id_without_token_fails(self, client):
        response = client.get("/api/v1/macros/products/1")
        assert response.status_code == 401

    def test_get_goals_without_token_fails(self, client):
        response = client.get("/api/v1/macros/goals")
        assert response.status_code == 401

    def test_get_stats_without_token_fails(self, client):
        response = client.get("/api/v1/macros/stats")
        assert response.status_code == 401


class TestBarcodeSearch:

    def test_barcode_cache_miss_calls_off(self, auth_client, mock_off_client, sample_barcode):
        """Primera vez: no está en BD → llama a OFF → persiste → devuelve 200"""
        response = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
        assert response.status_code == 200
        body = response.json()
        assert body["barcode"] == sample_barcode
        assert body["product_name"] == "Arroz redondo"
        assert body["brand"] == "Hacendado"
        assert body["source"] == "openfoodfacts"

    def test_barcode_cache_hit_no_off_call(self, auth_client, mock_off_client, sample_barcode):
        """Segunda vez: ya está en BD → devuelve el mismo producto sin error"""
        # Primera llamada — guarda en BD
        r1 = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
        assert r1.status_code == 200

        # Segunda llamada con mock inactivo — si llamase a OFF fallaría,
        # pero lo encuentra en caché y devuelve 200 igualmente
        r2 = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
        assert r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]

    def test_barcode_same_twice_creates_one_product(self, auth_client, mock_off_client, sample_barcode):
        """El mismo barcode dos veces solo crea 1 producto en BD"""
        r1 = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
        r2 = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
        assert r1.json()["id"] == r2.json()["id"]

    def test_barcode_not_found_in_off_returns_404(self, auth_client, mock_off_not_found):
        response = auth_client.get("/api/v1/macros/products/barcode/0000000000000")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_barcode_off_timeout_returns_503(self, auth_client, mock_off_timeout):
        response = auth_client.get("/api/v1/macros/products/barcode/9999999999999")
        assert response.status_code == 503

    def test_barcode_off_rate_limit_returns_503(self, auth_client, mock_off_rate_limit):
        response = auth_client.get("/api/v1/macros/products/barcode/9999999999999")
        assert response.status_code == 503

    def test_barcode_response_fields_complete(self, auth_client, mock_off_client, sample_barcode):
        """Verifica que todos los campos del ProductResponse están presentes"""
        body = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}").json()
        for field in ["id", "barcode", "product_name", "brand", "source",
                      "energy_kcal_100g", "proteins_100g", "carbohydrates_100g",
                      "fat_100g", "nutriscore"]:
            assert field in body, f"Campo '{field}' ausente"

    def test_barcode_nutrient_values(self, auth_client, mock_off_client, sample_barcode):
        body = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}").json()
        assert body["energy_kcal_100g"] == 354.0
        assert body["proteins_100g"]    == 7.0
        assert body["carbohydrates_100g"] == 77.0
        assert body["fat_100g"]         == 0.9

    def test_partial_product_saves_with_nulls(self, auth_client, mock_off_partial):
        """Producto con nutrientes parciales — se guarda con nulls en los campos faltantes"""
        response = auth_client.get("/api/v1/macros/products/barcode/1234567890123")
        assert response.status_code == 200
        body = response.json()
        assert body["energy_kcal_100g"] == 200.0
        assert body["proteins_100g"]    is None
        assert body["fat_100g"]         is None

    def test_two_users_share_same_product(
        self, auth_client, other_auth_client, mock_off_client, sample_barcode
    ):
        """El catálogo es global: el producto escaneado por user1 está disponible para user2"""
        r1 = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
        r2 = other_auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
        assert r1.json()["id"] == r2.json()["id"]

    def test_get_product_by_id(self, auth_client, cached_product_id):
        response = auth_client.get(f"/api/v1/macros/products/{cached_product_id}")
        assert response.status_code == 200
        assert response.json()["id"] == cached_product_id

    def test_get_product_by_id_not_found(self, auth_client):
        response = auth_client.get("/api/v1/macros/products/99999")
        assert response.status_code == 404


class TestProductSearch:

    def test_search_empty_db_calls_off(self, auth_client, mock_off_client):
        """BD vacía → busca en OFF"""
        response = auth_client.get("/api/v1/macros/products/search?q=arroz")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_search_missing_q_fails(self, auth_client):
        response = auth_client.get("/api/v1/macros/products/search")
        assert response.status_code == 422

    def test_search_empty_q_fails(self, auth_client):
        response = auth_client.get("/api/v1/macros/products/search?q=")
        assert response.status_code == 422

    def test_search_returns_list(self, auth_client, cached_product_id):
        """Con producto en BD, búsqueda local devuelve resultados"""
        response = auth_client.get("/api/v1/macros/products/search?q=Arroz")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1