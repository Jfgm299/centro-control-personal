"""
Tests for album CRUD, reorder, cover and ownership.
~14 tests.
"""
import pytest


TRIPS_BASE  = "/api/v1/travels/trips"
ALBUMS_BASE = "/api/v1/travels/albums"


class TestAlbums:
    """CRUD, reorder, cover, ownership."""

    def test_create_album(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        response = auth_client.post(
            f"{TRIPS_BASE}/{trip_id}/albums/",
            json={"name": "Paisajes", "position": 0},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Paisajes"
        assert data["trip_id"] == trip_id

    def test_list_albums_ordered_by_position(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        for i, name in enumerate(["Comida", "Dia 2", "Dia 1"]):
            auth_client.post(
                f"{TRIPS_BASE}/{trip_id}/albums/",
                json={"name": name, "position": i},
            )
        response = auth_client.get(f"{TRIPS_BASE}/{trip_id}/albums/")
        assert response.status_code == 200
        positions = [a["position"] for a in response.json()]
        assert positions == sorted(positions)

    def test_get_album_by_id(self, auth_client, created_album):
        album_id = created_album["id"]
        response = auth_client.get(f"{ALBUMS_BASE}/{album_id}")
        assert response.status_code == 200
        assert response.json()["id"] == album_id

    def test_update_album(self, auth_client, created_album):
        album_id = created_album["id"]
        response = auth_client.patch(
            f"{ALBUMS_BASE}/{album_id}",
            json={"name": "Nombre Nuevo"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Nombre Nuevo"

    def test_delete_album(self, auth_client, created_trip, mock_storage):
        trip_id = created_trip["id"]
        album = auth_client.post(
            f"{TRIPS_BASE}/{trip_id}/albums/",
            json={"name": "Para Borrar"},
        ).json()
        response = auth_client.delete(f"{ALBUMS_BASE}/{album['id']}")
        assert response.status_code == 204
        assert auth_client.get(f"{ALBUMS_BASE}/{album['id']}").status_code == 404

    def test_delete_album_calls_r2_cleanup(self, auth_client, created_album, mock_storage):
        album_id = created_album["id"]
        auth_client.delete(f"{ALBUMS_BASE}/{album_id}")
        mock_storage.delete_objects_by_prefix.assert_called_once()

    def test_reorder_albums(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        albums = []
        for i in range(3):
            a = auth_client.post(
                f"{TRIPS_BASE}/{trip_id}/albums/",
                json={"name": f"Album {i}", "position": i},
            ).json()
            albums.append(a)

        # Reverse order
        new_order = [
            {"album_id": albums[0]["id"], "position": 2},
            {"album_id": albums[1]["id"], "position": 1},
            {"album_id": albums[2]["id"], "position": 0},
        ]
        response = auth_client.post(
            f"{TRIPS_BASE}/{trip_id}/albums/reorder",
            json=new_order,
        )
        assert response.status_code == 200

    def test_set_album_cover(self, auth_client, created_album, uploaded_photo, mock_storage):
        album_id = created_album["id"]
        photo_id = uploaded_photo["id"]
        response = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/cover?photo_id={photo_id}"
        )
        assert response.status_code == 200
        assert response.json()["cover_photo_url"] is not None

    def test_create_album_in_nonexistent_trip_returns_404(self, auth_client):
        response = auth_client.post(
            f"{TRIPS_BASE}/999999/albums/",
            json={"name": "Ghosted"},
        )
        assert response.status_code == 404

    def test_get_nonexistent_album_returns_404(self, auth_client):
        assert auth_client.get(f"{ALBUMS_BASE}/999999").status_code == 404

    def test_other_user_cannot_get_album(self, auth_client, other_auth_client, created_album):
        album_id = created_album["id"]
        assert other_auth_client.get(f"{ALBUMS_BASE}/{album_id}").status_code == 404

    def test_other_user_cannot_update_album(self, auth_client, other_auth_client, created_album):
        album_id = created_album["id"]
        assert other_auth_client.patch(
            f"{ALBUMS_BASE}/{album_id}", json={"name": "Hacked"}
        ).status_code == 404

    def test_other_user_cannot_delete_album(self, auth_client, other_auth_client, created_album, mock_storage):
        album_id = created_album["id"]
        assert other_auth_client.delete(f"{ALBUMS_BASE}/{album_id}").status_code == 404

    def test_empty_album_list(self, auth_client, created_trip):
        trip_id = created_trip["id"]
        response = auth_client.get(f"{TRIPS_BASE}/{trip_id}/albums/")
        assert response.status_code == 200
        assert response.json() == []