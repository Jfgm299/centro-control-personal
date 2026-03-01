"""
Tests for activity CRUD and ownership.
~10 tests.
"""
import pytest


def activities_url(trip_id):
    return f"/api/v1/travels/trips/{trip_id}/activities"


class TestActivities:
    """CRUD, validation and ownership for activities."""

    def test_create_activity_minimal(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        response = auth_client.post(
            activities_url(trip_id) + "/",
            json={"title": "Visita al templo"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Visita al templo"
        assert data["trip_id"] == trip_id

    def test_create_activity_full(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        response = auth_client.post(
            activities_url(trip_id) + "/",
            json={
                "title":       "Cena en Shibuya",
                "category":    "food",
                "description": "Ramen increible",
                "date":        "2024-03-12",
                "lat":         35.6580,
                "lon":         139.7016,
                "rating":      5,
                "position":    0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "food"
        assert data["rating"] == 5

    def test_list_activities(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        for title in ["Actividad A", "Actividad B", "Actividad C"]:
            auth_client.post(
                activities_url(trip_id) + "/",
                json={"title": title},
            )
        response = auth_client.get(activities_url(trip_id) + "/")
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_update_activity(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        activity = auth_client.post(
            activities_url(trip_id) + "/",
            json={"title": "Original"},
        ).json()
        response = auth_client.patch(
            activities_url(trip_id) + f"/{activity['id']}",
            json={"title": "Actualizada", "rating": 4},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Actualizada"
        assert response.json()["rating"] == 4

    def test_delete_activity(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        activity = auth_client.post(
            activities_url(trip_id) + "/",
            json={"title": "Para Borrar"},
        ).json()
        response = auth_client.delete(
            activities_url(trip_id) + f"/{activity['id']}"
        )
        assert response.status_code == 204

        # Activity must no longer appear in the list
        listing = auth_client.get(activities_url(trip_id) + "/")
        ids = [a["id"] for a in listing.json()]
        assert activity["id"] not in ids

    def test_invalid_rating_returns_422(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        response = auth_client.post(
            activities_url(trip_id) + "/",
            json={"title": "Mala nota", "rating": 10},
        )
        assert response.status_code == 422

    def test_invalid_category_returns_422(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        response = auth_client.post(
            activities_url(trip_id) + "/",
            json={"title": "Mala cat", "category": "invalid_category"},
        )
        assert response.status_code == 422

    def test_activities_in_nonexistent_trip_returns_404(self, auth_client):
        assert auth_client.get(activities_url(999999) + "/").status_code == 404

    def test_other_user_cannot_list_activities(
        self, auth_client, other_auth_client, created_trip
    ):
        trip_id = created_trip["id"]
        assert other_auth_client.get(activities_url(trip_id) + "/").status_code == 404

    def test_other_user_cannot_delete_activity(
        self, auth_client, other_auth_client, created_trip
    ):
        trip_id = created_trip["id"]
        activity = auth_client.post(
            activities_url(trip_id) + "/",
            json={"title": "Privada"},
        ).json()
        assert other_auth_client.delete(
            activities_url(trip_id) + f"/{activity['id']}"
        ).status_code == 404