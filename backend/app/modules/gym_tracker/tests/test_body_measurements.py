class TestAuth:

    def test_get_measures_without_token_fails(self, client):
        response = client.get("/api/v1/body-measures/")
        assert response.status_code == 401

    def test_create_measure_without_token_fails(self, client):
        response = client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})
        assert response.status_code == 401

    def test_get_measure_by_id_without_token_fails(self, client, auth_client, body_measurement_id):
        response = client.get(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 401

    def test_delete_measure_without_token_fails(self, client, auth_client, body_measurement_id):
        response = client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 401


class TestOwnership:

    def test_cannot_get_other_users_measure(self, auth_client, other_auth_client, body_measurement_id):
        response = other_auth_client.get(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 404

    def test_cannot_delete_other_users_measure(self, auth_client, other_auth_client, body_measurement_id):
        response = other_auth_client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 404

    def test_users_see_only_their_measures(self, auth_client, other_auth_client, body_measurement_id):
        other_auth_client.post("/api/v1/body-measures/", json={"weight_kg": 80.0})
        response = auth_client.get("/api/v1/body-measures/")
        assert len(response.json()) == 1

    def test_other_user_measures_not_in_list(self, auth_client, other_auth_client):
        other_auth_client.post("/api/v1/body-measures/", json={"weight_kg": 80.0})
        response = auth_client.get("/api/v1/body-measures/")
        assert response.json() == []


class TestGetBodyMeasurements:

    def test_get_measures_empty(self, auth_client):
        response = auth_client.get("/api/v1/body-measures/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_measures_returns_list(self, auth_client, body_measurement_id):
        response = auth_client.get("/api/v1/body-measures/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_measures_multiple(self, auth_client):
        auth_client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})
        auth_client.post("/api/v1/body-measures/", json={"weight_kg": 74.5})
        response = auth_client.get("/api/v1/body-measures/")
        assert len(response.json()) == 2

    def test_get_measures_response_fields(self, auth_client, body_measurement_id):
        response = auth_client.get("/api/v1/body-measures/")
        item = response.json()[0]
        assert "id" in item
        assert "weight_kg" in item
        assert "body_fat_percent" in item
        assert "notes" in item
        assert "created_at" in item

    def test_get_measures_ordered_by_creation(self, auth_client):
        auth_client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})
        auth_client.post("/api/v1/body-measures/", json={"weight_kg": 74.5})
        response = auth_client.get("/api/v1/body-measures/")
        ids = [m["id"] for m in response.json()]
        assert ids == sorted(ids)


class TestCreateBodyMeasurement:

    def test_create_measurement_success(self, auth_client):
        data = {"weight_kg": 75.0, "body_fat_percent": 15.0, "notes": "Morning"}
        response = auth_client.post("/api/v1/body-measures/", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["weight_kg"] == 75.0
        assert body["body_fat_percent"] == 15.0
        assert body["notes"] == "Morning"
        assert body["created_at"] is not None

    def test_create_measurement_only_weight(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 80.0})
        assert response.status_code == 201
        body = response.json()
        assert body["weight_kg"] == 80.0
        assert body["body_fat_percent"] is None
        assert body["notes"] is None

    def test_create_measurement_without_notes(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": 12.0})
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_create_measurement_zero_body_fat(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": 0.0})
        assert response.status_code == 201
        assert response.json()["body_fat_percent"] == 0.0

    def test_create_measurement_max_body_fat(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": 100.0})
        assert response.status_code == 201
        assert response.json()["body_fat_percent"] == 100.0

    def test_create_measurement_body_fat_above_100_fails(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": 101.0})
        assert response.status_code == 422

    def test_create_measurement_negative_body_fat_fails(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 70.0, "body_fat_percent": -1.0})
        assert response.status_code == 422

    def test_create_measurement_zero_weight_fails(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 0.0})
        assert response.status_code == 422

    def test_create_measurement_negative_weight_fails(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": -5.0})
        assert response.status_code == 422

    def test_create_measurement_missing_weight_fails(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"body_fat_percent": 15.0})
        assert response.status_code == 422

    def test_create_measurement_decimal_weight(self, auth_client):
        response = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 74.35})
        assert response.status_code == 201
        assert response.json()["weight_kg"] == 74.35

    def test_create_multiple_measurements(self, auth_client):
        for i in range(5):
            r = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 75.0 - i * 0.1})
            assert r.status_code == 201
        response = auth_client.get("/api/v1/body-measures/")
        assert len(response.json()) == 5

    def test_create_measurement_ids_increment(self, auth_client):
        r1 = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})
        r2 = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 74.5})
        assert r2.json()["id"] > r1.json()["id"]


class TestGetBodyMeasurementById:

    def test_get_measurement_success(self, auth_client, body_measurement_id):
        response = auth_client.get(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 200
        assert response.json()["id"] == body_measurement_id

    def test_get_measurement_not_found(self, auth_client):
        response = auth_client.get("/api/v1/body-measures/99999")
        assert response.status_code == 404

    def test_get_measurement_response_fields(self, auth_client, body_measurement_id):
        response = auth_client.get(f"/api/v1/body-measures/{body_measurement_id}")
        body = response.json()
        assert "id" in body
        assert "weight_kg" in body
        assert "body_fat_percent" in body
        assert "notes" in body
        assert "created_at" in body

    def test_get_measurement_correct_data(self, auth_client):
        created = auth_client.post("/api/v1/body-measures/", json={
            "weight_kg": 72.5, "body_fat_percent": 14.0, "notes": "Post workout"
        })
        mid = created.json()["id"]
        response = auth_client.get(f"/api/v1/body-measures/{mid}")
        body = response.json()
        assert body["weight_kg"] == 72.5
        assert body["body_fat_percent"] == 14.0
        assert body["notes"] == "Post workout"


class TestDeleteBodyMeasurement:

    def test_delete_measurement_success(self, auth_client, body_measurement_id):
        response = auth_client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 204

    def test_delete_measurement_removes_it(self, auth_client, body_measurement_id):
        auth_client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        response = auth_client.get(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 404

    def test_delete_measurement_not_found(self, auth_client):
        response = auth_client.delete("/api/v1/body-measures/99999")
        assert response.status_code == 404

    def test_delete_measurement_twice_fails(self, auth_client, body_measurement_id):
        auth_client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        response = auth_client.delete(f"/api/v1/body-measures/{body_measurement_id}")
        assert response.status_code == 404

    def test_delete_one_measurement_preserves_others(self, auth_client):
        r1 = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})
        r2 = auth_client.post("/api/v1/body-measures/", json={"weight_kg": 74.5})
        id1 = r1.json()["id"]
        id2 = r2.json()["id"]
        auth_client.delete(f"/api/v1/body-measures/{id1}")
        response = auth_client.get("/api/v1/body-measures/")
        remaining = response.json()
        assert len(remaining) == 1
        assert remaining[0]["id"] == id2