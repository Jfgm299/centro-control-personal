"""
Tests for trip CRUD, map endpoint, auth and ownership.
~19 tests.
"""
import pytest


BASE = "/api/v1/travels/trips"


class TestAuth:
    """401 without token on every trip endpoint."""

    def test_list_trips_requires_auth(self, client):
        assert client.get(f"{BASE}/").status_code == 401

    def test_create_trip_requires_auth(self, client):
        assert client.post(f"{BASE}/", json={"title": "X", "destination": "Y"}).status_code == 401

    def test_get_trip_requires_auth(self, client):
        assert client.get(f"{BASE}/1").status_code == 401

    def test_update_trip_requires_auth(self, client):
        assert client.patch(f"{BASE}/1", json={"title": "X"}).status_code == 401

    def test_delete_trip_requires_auth(self, client):
        assert client.delete(f"{BASE}/1").status_code == 401

    def test_map_requires_auth(self, client):
        assert client.get(f"{BASE}/map").status_code == 401


class TestOwnership:
    """Resources of another user always return 404 — never 403."""

    def test_get_other_user_trip_returns_404(self, auth_client, other_auth_client, created_trip):
        trip_id = created_trip["id"]
        assert other_auth_client.get(f"{BASE}/{trip_id}").status_code == 404

    def test_update_other_user_trip_returns_404(self, auth_client, other_auth_client, created_trip):
        trip_id = created_trip["id"]
        assert other_auth_client.patch(f"{BASE}/{trip_id}", json={"title": "Hacked"}).status_code == 404

    def test_delete_other_user_trip_returns_404(self, auth_client, other_auth_client, created_trip, mock_storage):
        trip_id = created_trip["id"]
        assert other_auth_client.delete(f"{BASE}/{trip_id}").status_code == 404

    def test_other_user_not_in_list(self, auth_client, other_auth_client, created_trip):
        response = other_auth_client.get(f"{BASE}/")
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert created_trip["id"] not in ids


class TestTrips:
    """CRUD + validation + map endpoint."""

    def test_create_trip_minimal(self, auth_client):
        response = auth_client.post(
            f"{BASE}/",
            json={"title": "Viaje Minimo", "destination": "Madrid"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Viaje Minimo"
        assert data["lat"] is None
        assert data["lon"] is None

    def test_create_trip_full(self, auth_client, created_trip):
        assert created_trip["title"] == "Test Trip"
        assert created_trip["lat"] == 35.6762
        assert created_trip["lon"] == 139.6503
        assert created_trip["country_code"] == "JP"

    def test_list_trips(self, auth_client, created_trip):
        response = auth_client.get(f"{BASE}/")
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()]
        assert created_trip["id"] in ids

    def test_get_trip_by_id(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        response = auth_client.get(f"{BASE}/{trip_id}")
        assert response.status_code == 200
        assert response.json()["id"] == trip_id

    def test_update_trip_partial(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        response = auth_client.patch(
            f"{BASE}/{trip_id}",
            json={"title": "Titulo Actualizado"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Titulo Actualizado"
        # Other fields unchanged
        assert response.json()["destination"] == "Tokio, Japon"

    def test_delete_trip(self, auth_client, mock_storage):
        trip = auth_client.post(
            f"{BASE}/",
            json={"title": "Para Borrar", "destination": "Nowhere"},
        ).json()
        response = auth_client.delete(f"{BASE}/{trip['id']}")
        assert response.status_code == 204
        assert auth_client.get(f"{BASE}/{trip['id']}").status_code == 404

    def test_delete_trip_calls_r2_cleanup(self, auth_client, mock_storage, created_trip):
        trip_id = created_trip["id"]
        auth_client.delete(f"{BASE}/{trip_id}")
        mock_storage.delete_objects_by_prefix.assert_called_once()

    def test_invalid_lat_returns_422(self, auth_client):
        response = auth_client.post(
            f"{BASE}/",
            json={"title": "Bad Coords", "destination": "X", "lat": 999},
        )
        assert response.status_code == 422

    def test_invalid_lon_returns_422(self, auth_client):
        response = auth_client.post(
            f"{BASE}/",
            json={"title": "Bad Coords", "destination": "X", "lon": -999},
        )
        assert response.status_code == 422

    def test_invalid_date_range_returns_422(self, auth_client):
        response = auth_client.post(
            f"{BASE}/",
            json={
                "title":      "Bad Dates",
                "destination": "X",
                "start_date": "2025-12-31",
                "end_date":   "2025-01-01",
            },
        )
        assert response.status_code == 422

    def test_map_returns_only_trips_with_coords(self, auth_client, created_trip, created_trip_no_coords):
        response = auth_client.get(f"{BASE}/map")
        assert response.status_code == 200
        data = response.json()
        ids = [t["id"] for t in data]
        assert created_trip["id"] in ids
        assert created_trip_no_coords["id"] not in ids

    def test_map_response_shape(self, auth_client, created_trip):
        response = auth_client.get(f"{BASE}/map")
        assert response.status_code == 200
        item = next(t for t in response.json() if t["id"] == created_trip["id"])
        assert "lat" in item
        assert "lon" in item
        assert "title" in item
        assert "destination" in item

    def test_get_nonexistent_trip_returns_404(self, auth_client):
        assert auth_client.get(f"{BASE}/999999").status_code == 404