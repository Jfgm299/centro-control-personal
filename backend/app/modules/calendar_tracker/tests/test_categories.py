import pytest


class TestCategoriesAuth:

    def test_list_without_token_fails(self, client):
        assert client.get("/api/v1/calendar/categories").status_code == 401

    def test_create_without_token_fails(self, client):
        assert client.post("/api/v1/calendar/categories", json={}).status_code == 401


class TestCategoriesOwnership:

    def test_users_see_only_their_categories(self, auth_client, other_auth_client, category_id):
        response = other_auth_client.get("/api/v1/calendar/categories")
        ids = [c["id"] for c in response.json()]
        assert category_id not in ids

    def test_cannot_update_other_users_category(self, auth_client, other_auth_client, category_id):
        response = other_auth_client.patch(
            f"/api/v1/calendar/categories/{category_id}",
            json={"name": "Hackeado"},
        )
        assert response.status_code == 404

    def test_cannot_delete_other_users_category(self, auth_client, other_auth_client, category_id):
        assert other_auth_client.delete(
            f"/api/v1/calendar/categories/{category_id}"
        ).status_code == 404


class TestCreateCategory:

    def test_create_success(self, auth_client, category_data):
        response = auth_client.post("/api/v1/calendar/categories", json=category_data)
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == category_data["name"]
        assert body["icon"] == category_data["icon"]
        assert body["color"].startswith("#")
        assert len(body["color"]) == 7

    def test_create_assigns_random_color(self, auth_client):
        r1 = auth_client.post("/api/v1/calendar/categories", json={"name": "Cat1"}).json()
        r2 = auth_client.post("/api/v1/calendar/categories", json={"name": "Cat2"}).json()
        # Ambas tienen color válido
        assert r1["color"].startswith("#")
        assert r2["color"].startswith("#")

    def test_create_with_explicit_color(self, auth_client):
        response = auth_client.post("/api/v1/calendar/categories", json={
            "name": "Con color", "color": "#FF0000",
        })
        assert response.status_code == 201
        assert response.json()["color"] == "#FF0000"

    def test_create_invalid_color_fails(self, auth_client):
        response = auth_client.post("/api/v1/calendar/categories", json={
            "name": "Mala", "color": "rojo",
        })
        assert response.status_code == 422

    def test_create_duplicate_name_fails(self, auth_client, category_id, category_data):
        response = auth_client.post("/api/v1/calendar/categories", json=category_data)
        assert response.status_code == 409

    def test_create_empty_name_fails(self, auth_client):
        assert auth_client.post(
            "/api/v1/calendar/categories", json={"name": ""}
        ).status_code == 422

    def test_create_with_dnd_defaults(self, auth_client):
        response = auth_client.post("/api/v1/calendar/categories", json={
            "name": "Trabajo",
            "default_enable_dnd": True,
            "default_reminder_minutes": 10,
        })
        assert response.status_code == 201
        body = response.json()
        assert body["default_enable_dnd"] is True
        assert body["default_reminder_minutes"] == 10


class TestUpdateCategory:

    def test_update_name(self, auth_client, category_id):
        response = auth_client.patch(
            f"/api/v1/calendar/categories/{category_id}",
            json={"name": "Universidad 2"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Universidad 2"

    def test_update_color(self, auth_client, category_id):
        response = auth_client.patch(
            f"/api/v1/calendar/categories/{category_id}",
            json={"color": "#00FF00"},
        )
        assert response.status_code == 200
        assert response.json()["color"] == "#00FF00"

    def test_update_nonexistent_fails(self, auth_client):
        assert auth_client.patch(
            "/api/v1/calendar/categories/99999", json={"name": "X"}
        ).status_code == 404

    def test_update_to_duplicate_name_fails(self, auth_client, category_id, second_category_id):
        second_name = auth_client.get("/api/v1/calendar/categories").json()
        second_name = next(c["name"] for c in second_name if c["id"] == second_category_id)
        response = auth_client.patch(
            f"/api/v1/calendar/categories/{category_id}",
            json={"name": second_name},
        )
        assert response.status_code == 409


class TestDeleteCategory:

    def test_delete_success(self, auth_client, category_id):
        assert auth_client.delete(
            f"/api/v1/calendar/categories/{category_id}"
        ).status_code == 204

    def test_delete_removes_category(self, auth_client, category_id):
        auth_client.delete(f"/api/v1/calendar/categories/{category_id}")
        ids = [c["id"] for c in auth_client.get("/api/v1/calendar/categories").json()]
        assert category_id not in ids

    def test_delete_twice_fails(self, auth_client, category_id):
        auth_client.delete(f"/api/v1/calendar/categories/{category_id}")
        assert auth_client.delete(
            f"/api/v1/calendar/categories/{category_id}"
        ).status_code == 404

    def test_delete_nonexistent_fails(self, auth_client):
        assert auth_client.delete(
            "/api/v1/calendar/categories/99999"
        ).status_code == 404