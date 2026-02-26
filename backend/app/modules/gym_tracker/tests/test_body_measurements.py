class TestGetBodyMeasurements:

    def test_get_measures_empty(self, client):
        response = client.get("/api/v1/body-measures/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_measures_returns_list(self, client, body_measurement_id):
        response = client.get("/api/v1/body-measures/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_measures_multiple(self, client):
        client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})
        client.post("/api/v1/body-measures/", json={"weight_kg": 74.5})
        response = client.get("/api/v1/body-measures/")
        assert len(response.json()) == 2

    def test_get_measures_response_fields(self, client, body_measurement_id):
        response = client.get("/api/v1/body-measures/")
        item = response.json()[0]
        assert "id" in item
        assert "weight_kg" in item
        assert "body_fat_percent" in item
        assert "notes" in item
        assert "created_at" in item


class TestCreateBodyMeasurement:

    def test_create_measurement_success(self, client):
        data = {"weight_kg": 75.0, "body_fat_percent": 15.0, "notes": "Morning"}
        response = client.post("/api/v1/body-measures/", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["weight_kg"] == 75.0
        assert body["body_fat_percent"] == 15.0
        assert body["notes"] == "Morning"
        assert body["created_at"] is not None

    def test_create_measurement_only_weight(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 80.0})
        assert response.status_code == 201
        body = response.json()
        assert body["weight_kg"] == 80.0
        assert body["body_fat_percent"] is None
        assert body["notes"] is None

    def test_create_measurement_without_notes(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": 12.0})
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_create_measurement_zero_body_fat(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": 0.0})
        assert response.status_code == 201
        assert response.json()["body_fat_percent"] == 0.0

    def test_create_measurement_max_body_fat(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": 100.0})
        assert response.status_code == 201
        assert response.json()["body_fat_percent"] == 100.0

    def test_create_measurement_body_fat_above_100_fails(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": 101.0})
        assert response.status_code == 422

    def test_create_measurement_negative_body_fat_fails(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": -1.0})
        assert response.status_code == 422

    def test_create_measurement_zero_weight_fails(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 0.0})
        assert response.status_code == 422

    def test_create_measurement_negative_weight_fails(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": -5.0})
        assert response.status_code == 422

    def test_create_measurement_missing_weight_fails(self, client):
        response = client.post("/api/v1/body-measures/", json={"body_fat_percent": 15.0})
        assert response.status_code == 422

    def test_create_measurement_decimal_weight(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 74.35})
        assert response.status_code == 201
        assert response.json()["weight_kg"] == 74.35

    def test_create_multiple_measurements(self, client):
        for i in range(5):
            r = client.post("/api/v1/body-measures/", json={"weight_kg": 75.0 - i * 0.1})
            assert r.status_code == 201
        response = client.get("/api/v1/body-measures/")
        assert len(response.json()) == 5

    def test_create_measurement_ids_increment(self, client):
        r1 = client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})
        r2 = client.post("/api/v1/body-measures/", json={"weight_kg": 74.5})
        assert r2.json()["id"] > r1.json()["id"]


class TestGetBodyMeasurementById:

    def test_get_measurement_success(self, client, body_measurement_id):
        response = client.get(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 200
        assert response.json()["id"] == body_measurement_id

    def test_get_measurement_not_found(self, client):
        response = client.get("/api/v1/body-measures/99999")
        assert response.status_code == 404

    def test_get_measurement_response_fields(self, client, body_measurement_id):
        response = client.get(f"/api/v1/body-measures/{body_measurement_id}")
        body = response.json()
        assert "id" in body
        assert "weight_kg" in body
        assert "body_fat_percent" in body
        assert "notes" in body
        assert "created_at" in body

    def test_get_measurement_correct_data(self, client):
        created = client.post("/api/v1/body-measures/", json={
            "weight_kg": 72.5, "body_fat_percent": 14.0, "notes": "Post workout"
        })
        mid = created.json()["id"]
        response = client.get(f"/api/v1/body-measures/{mid}")
        body = response.json()
        assert body["weight_kg"] == 72.5
        assert body["body_fat_percent"] == 14.0
        assert body["notes"] == "Post workout"


class TestDeleteBodyMeasurement:

    def test_delete_measurement_success(self, client, body_measurement_id):
        response = client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 204

    def test_delete_measurement_removes_it(self, client, body_measurement_id):
        client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        response = client.get(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 404

    def test_delete_measurement_not_found(self, client):
        response = client.delete("/api/v1/body-measures/99999")
        assert response.status_code == 404

    def test_delete_measurement_twice_fails(self, client, body_measurement_id):
        client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        response = client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 404

    def test_delete_one_measurement_preserves_others(self, client):
        r1 = client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})
        r2 = client.post("/api/v1/body-measures/", json={"weight_kg": 74.5})
        id1 = r1.json()["id"]
        id2 = r2.json()["id"]

        client.delete(f"/api/v1/body-measures/{id1}")
        response = client.get("/api/v1/body-measures/")
        remaining = response.json()
        assert len(remaining) == 1
        assert remaining[0]["id"] == id2