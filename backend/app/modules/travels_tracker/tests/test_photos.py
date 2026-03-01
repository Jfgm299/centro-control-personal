"""
Tests for photo upload flow, management and favorites.
~25 tests. StorageService always mocked via fixture.
"""
import pytest


ALBUMS_BASE = "/api/v1/travels/albums"
PHOTOS_BASE = "/api/v1/travels/photos"
TRIPS_BASE  = "/api/v1/travels/trips"


class TestPhotoUpload:
    """Upload flow: request presigned URL → confirm."""

    def test_request_upload_url_returns_200(self, auth_client, created_album, mock_storage):
        album_id = created_album["id"]
        response = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "foto.jpg", "content_type": "image/jpeg"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert "photo_id" in data
        assert "r2_key" in data
        assert data["expires_in"] == 600

    def test_request_upload_url_creates_pending_photo(self, auth_client, created_album, mock_storage):
        album_id = created_album["id"]
        response = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "foto.jpg", "content_type": "image/jpeg"},
        )
        # Pending photos are NOT visible in listings
        photo_id = response.json()["photo_id"]
        listing = auth_client.get(f"{ALBUMS_BASE}/{album_id}/photos/")
        ids = [p["id"] for p in listing.json()]
        assert photo_id not in ids

    def test_confirm_upload_marks_photo_uploaded(self, auth_client, created_album, mock_storage):
        album_id = created_album["id"]
        req = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "foto.jpg", "content_type": "image/jpeg"},
        )
        photo_id = req.json()["photo_id"]
        confirm = auth_client.post(
            f"{PHOTOS_BASE}/{photo_id}/confirm",
            json={"size_bytes": 204800, "width": 1920, "height": 1080},
        )
        assert confirm.status_code == 200
        assert confirm.json()["status"] == "uploaded"
        assert confirm.json()["public_url"] is not None

    def test_confirm_upload_when_not_in_r2_returns_400(
        self, auth_client, created_album, mock_storage_not_exists
    ):
        album_id = created_album["id"]
        req = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "foto.jpg", "content_type": "image/jpeg"},
        )
        photo_id = req.json()["photo_id"]
        response = auth_client.post(
            f"{PHOTOS_BASE}/{photo_id}/confirm",
            json={"size_bytes": 1024},
        )
        assert response.status_code == 400

    def test_confirm_already_confirmed_returns_409(self, auth_client, uploaded_photo):
        photo_id = uploaded_photo["id"]
        # Second confirm attempt
        response = auth_client.post(
            f"{PHOTOS_BASE}/{photo_id}/confirm",
            json={"size_bytes": 1024},
        )
        assert response.status_code == 409

    def test_invalid_content_type_returns_422(self, auth_client, created_album, mock_storage):
        album_id = created_album["id"]
        response = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "doc.pdf", "content_type": "application/pdf"},
        )
        assert response.status_code == 422

    def test_allowed_content_types(self, auth_client, created_album, mock_storage):
        album_id = created_album["id"]
        for ct in ["image/jpeg", "image/png", "image/webp", "image/heic"]:
            response = auth_client.post(
                f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
                json={"filename": "foto.jpg", "content_type": ct},
            )
            assert response.status_code == 200, f"Failed for {ct}"

    def test_upload_to_nonexistent_album_returns_404(self, auth_client, mock_storage):
        response = auth_client.post(
            f"{ALBUMS_BASE}/999999/photos/upload-url",
            json={"filename": "foto.jpg", "content_type": "image/jpeg"},
        )
        assert response.status_code == 404

    def test_photo_limit_enforced(self, auth_client, created_album, mock_storage):
        """After 30 uploaded photos, the 31st request must return 422."""
        album_id  = created_album["id"]
        trip_id   = created_album["trip_id"]

        for i in range(30):
            req = auth_client.post(
                f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
                json={"filename": f"foto_{i}.jpg", "content_type": "image/jpeg"},
            )
            assert req.status_code == 200, f"Upload {i} failed"
            pid = req.json()["photo_id"]
            confirm = auth_client.post(
                f"{PHOTOS_BASE}/{pid}/confirm",
                json={"size_bytes": 10000},
            )
            assert confirm.status_code == 200, f"Confirm {i} failed"

        # 31st must fail
        response = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "foto_31.jpg", "content_type": "image/jpeg"},
        )
        assert response.status_code == 422

    def test_pending_photos_dont_count_toward_limit(self, auth_client, created_album, mock_storage):
        """Pending photos (not confirmed) must not count toward the 30-photo limit."""
        album_id = created_album["id"]

        # Create 30 PENDING photos (don't confirm any)
        for i in range(30):
            req = auth_client.post(
                f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
                json={"filename": f"pending_{i}.jpg", "content_type": "image/jpeg"},
            )
            assert req.status_code == 200

        # The 31st request should still succeed because none were confirmed
        response = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "still_ok.jpg", "content_type": "image/jpeg"},
        )
        assert response.status_code == 200


class TestPhotoManage:
    """Listing, update, delete and reorder of confirmed photos."""

    def test_list_photos_returns_only_uploaded(self, auth_client, created_album, mock_storage):
        album_id = created_album["id"]

        # Create one pending (not confirmed)
        auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "pending.jpg", "content_type": "image/jpeg"},
        )

        # Create one confirmed
        req = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "confirmed.jpg", "content_type": "image/jpeg"},
        )
        pid = req.json()["photo_id"]
        auth_client.post(f"{PHOTOS_BASE}/{pid}/confirm", json={"size_bytes": 1024})

        response = auth_client.get(f"{ALBUMS_BASE}/{album_id}/photos/")
        assert response.status_code == 200
        statuses = [p["status"] for p in response.json()]
        assert all(s == "uploaded" for s in statuses)
        assert len(statuses) == 1

    def test_update_photo_caption(self, auth_client, uploaded_photo):
        photo_id = uploaded_photo["id"]
        response = auth_client.patch(
            f"{PHOTOS_BASE}/{photo_id}",
            json={"caption": "Mi foto favorita"},
        )
        assert response.status_code == 200
        assert response.json()["caption"] == "Mi foto favorita"

    def test_delete_photo(self, auth_client, uploaded_photo, mock_storage):
        photo_id = uploaded_photo["id"]
        response = auth_client.delete(f"{PHOTOS_BASE}/{photo_id}")
        assert response.status_code == 204
        mock_storage.delete_object.assert_called_once()

    def test_reorder_photos(self, auth_client, multiple_photos, created_album):
        album_id = created_album["id"]
        photos   = multiple_photos

        new_order = [
            {"photo_id": p["id"], "position": len(photos) - 1 - i}
            for i, p in enumerate(photos)
        ]
        response = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/reorder",
            json=new_order,
        )
        assert response.status_code == 200

    def test_get_nonexistent_album_photos_returns_404(self, auth_client):
        assert auth_client.get(f"{ALBUMS_BASE}/999999/photos/").status_code == 404

    def test_other_user_cannot_update_photo(self, auth_client, other_auth_client, uploaded_photo):
        photo_id = uploaded_photo["id"]
        assert other_auth_client.patch(
            f"{PHOTOS_BASE}/{photo_id}",
            json={"caption": "Hacked"},
        ).status_code == 404

    def test_other_user_cannot_delete_photo(self, auth_client, other_auth_client, uploaded_photo, mock_storage):
        photo_id = uploaded_photo["id"]
        assert other_auth_client.delete(f"{PHOTOS_BASE}/{photo_id}").status_code == 404


class TestFavorites:
    """Toggle favorite and global favorites listing."""

    def test_toggle_favorite_on(self, auth_client, uploaded_photo):
        photo_id = uploaded_photo["id"]
        response = auth_client.post(f"{PHOTOS_BASE}/{photo_id}/favorite")
        assert response.status_code == 200
        assert response.json()["is_favorite"] is True

    def test_toggle_favorite_off(self, auth_client, favorite_photo):
        photo_id = favorite_photo["id"]
        # Toggle again to unfavorite
        response = auth_client.post(f"{PHOTOS_BASE}/{photo_id}/favorite")
        assert response.status_code == 200
        assert response.json()["is_favorite"] is False

    def test_favorites_listing(self, auth_client, favorite_photo):
        response = auth_client.get(f"{TRIPS_BASE}/favorites")
        assert response.status_code == 200
        ids = [p["id"] for p in response.json()]
        assert favorite_photo["id"] in ids

    def test_non_favorite_not_in_listing(self, auth_client, uploaded_photo):
        response = auth_client.get(f"{TRIPS_BASE}/favorites")
        assert response.status_code == 200
        ids = [p["id"] for p in response.json()]
        assert uploaded_photo["id"] not in ids

    def test_favorites_listing_requires_auth(self, client):
        assert client.get(f"{TRIPS_BASE}/favorites").status_code == 401

    def test_only_uploaded_photos_in_favorites(self, auth_client, created_album, mock_storage):
        """Pending photos cannot be favorited — endpoint returns 404."""
        album_id = created_album["id"]
        req = auth_client.post(
            f"{ALBUMS_BASE}/{album_id}/photos/upload-url",
            json={"filename": "pending.jpg", "content_type": "image/jpeg"},
        )
        pending_id = req.json()["photo_id"]
        # Trying to favorite a pending photo must fail
        response = auth_client.post(f"{PHOTOS_BASE}/{pending_id}/favorite")
        assert response.status_code == 404

    def test_other_user_favorites_are_isolated(
        self, auth_client, other_auth_client, favorite_photo
    ):
        response = other_auth_client.get(f"{TRIPS_BASE}/favorites")
        assert response.status_code == 200
        ids = [p["id"] for p in response.json()]
        assert favorite_photo["id"] not in ids