"""
Fixtures for travels_tracker tests.
StorageService is fully mocked — zero real R2 calls.
"""
import pytest
from unittest.mock import MagicMock, patch


# ── StorageService mocks ───────────────────────────────────────────────────────

from app.modules.travels_tracker.services.storage_service import StorageService

@pytest.fixture
def mock_storage():
    with patch(
        "app.modules.travels_tracker.services.storage_service.StorageService",
        autospec=True,
    ) as MockClass:
        instance = MockClass.return_value
        instance.generate_upload_url.return_value = (
            "https://fake-r2.example.com/presigned-put-url"
        )
        instance.object_exists.return_value = True
        instance.delete_object.return_value = None
        instance.delete_objects_by_prefix.return_value = None
        instance.build_public_url.side_effect = (
            lambda key: f"https://pub-fake.r2.dev/{key}"
        )

        # ← Añadir estas tres líneas — métodos estáticos puros, no tocan R2
        instance.build_photo_key.side_effect = StorageService.build_photo_key
        instance.build_trip_prefix.side_effect = StorageService.build_trip_prefix
        instance.build_album_prefix.side_effect = StorageService.build_album_prefix

        with patch(
            "app.modules.travels_tracker.services.trip_service.storage_service",
            instance,
        ), patch(
            "app.modules.travels_tracker.services.album_service.storage_service",
            instance,
        ), patch(
            "app.modules.travels_tracker.services.photo_service.storage_service",
            instance,
        ):
            yield instance


@pytest.fixture
def mock_storage_not_exists(mock_storage):
    """
    Variant where object_exists returns False.
    Used to test confirm_photo_upload when R2 upload never completed.
    """
    mock_storage.object_exists.return_value = False
    yield mock_storage


# ── Trip fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def created_trip(auth_client):
    """Creates a trip with coordinates and returns the full response dict."""
    response = auth_client.post(
        "/api/v1/travels/trips/",
        json={
            "title":       "Test Trip",
            "destination": "Tokio, Japon",
            "country_code": "JP",
            "lat":          35.6762,
            "lon":          139.6503,
            "start_date":  "2024-03-10",
            "end_date":    "2024-03-20",
            "description": "Un viaje de prueba",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def created_trip_no_coords(auth_client):
    """Creates a trip WITHOUT coordinates — should NOT appear on map."""
    response = auth_client.post(
        "/api/v1/travels/trips/",
        json={"title": "Sin Coordenadas", "destination": "Desconocido"},
    )
    assert response.status_code == 201
    return response.json()


# ── Album fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def created_album(auth_client, created_trip):
    """Creates an album inside created_trip and returns the full response dict."""
    trip_id = created_trip["id"]
    response = auth_client.post(
        f"/api/v1/travels/trips/{trip_id}/albums/",
        json={"name": "Dia 1", "description": "Primer dia en Tokio", "position": 0},
    )
    assert response.status_code == 201
    return response.json()


# ── Photo fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def uploaded_photo(auth_client, created_album, mock_storage):
    """
    Full upload flow (request + confirm) using mock_storage.
    Returns the confirmed PhotoResponse dict (status=uploaded).
    """
    album_id = created_album["id"]

    # Step 1: request presigned URL
    req = auth_client.post(
        f"/api/v1/travels/albums/{album_id}/photos/upload-url",
        json={"filename": "foto.jpg", "content_type": "image/jpeg"},
    )
    assert req.status_code == 200
    photo_id = req.json()["photo_id"]

    # Step 2: confirm upload
    confirm = auth_client.post(
        f"/api/v1/travels/photos/{photo_id}/confirm",
        json={"size_bytes": 204800, "width": 1920, "height": 1080},
    )
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "uploaded"
    return confirm.json()


@pytest.fixture
def multiple_photos(auth_client, created_album, mock_storage):
    """Creates 5 uploaded photos in created_album. Returns list of PhotoResponse dicts."""
    album_id = created_album["id"]
    photos = []
    for i in range(5):
        req = auth_client.post(
            f"/api/v1/travels/albums/{album_id}/photos/upload-url",
            json={"filename": f"foto_{i}.jpg", "content_type": "image/jpeg"},
        )
        assert req.status_code == 200
        photo_id = req.json()["photo_id"]

        confirm = auth_client.post(
            f"/api/v1/travels/photos/{photo_id}/confirm",
            json={"size_bytes": 100000 + i * 1000},
        )
        assert confirm.status_code == 200
        photos.append(confirm.json())
    return photos


@pytest.fixture
def favorite_photo(auth_client, uploaded_photo):
    """Returns an uploaded photo that has been toggled to is_favorite=True."""
    photo_id = uploaded_photo["id"]
    response = auth_client.post(f"/api/v1/travels/photos/{photo_id}/favorite")
    assert response.status_code == 200
    assert response.json()["is_favorite"] is True
    return response.json()