from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from ..schemas.photo_schema import (
    PhotoUploadRequest, PhotoUploadResponse,
    PhotoConfirmRequest, PhotoUpdate, PhotoReorderItem, PhotoResponse,
)
from ..services import photo_service

# Routers grouped by resource prefix
trips_router  = APIRouter(prefix="/travels/trips", tags=["Travels"])
albums_router = APIRouter(prefix="/travels/albums", tags=["Travels"])
photos_router = APIRouter(prefix="/travels/photos", tags=["Travels"])

router = APIRouter()


# ── CRITICAL ORDER: /favorites BEFORE /{photo_id} ─────────────────────────────

@trips_router.get("/favorites", response_model=list[PhotoResponse])
def get_favorites(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Global favorites collection across all trips."""
    return photo_service.get_favorites(db, user.id)


# ── Album-nested photo endpoints ───────────────────────────────────────────────

@albums_router.post("/{album_id}/photos/upload-url", response_model=PhotoUploadResponse)
def request_upload_url(
    album_id: int,
    data:     PhotoUploadRequest,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    """Step 1: Request a presigned PUT URL to upload directly to R2."""
    result = photo_service.request_photo_upload(db, user.id, album_id, data)
    return PhotoUploadResponse(**result)


@albums_router.get("/{album_id}/photos/", response_model=list[PhotoResponse])
def get_photos(
    album_id: int,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    return photo_service.get_photos(db, user.id, album_id)


@albums_router.post("/{album_id}/photos/reorder", response_model=list[PhotoResponse])
def reorder_photos(
    album_id: int,
    order:    list[PhotoReorderItem],
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    return photo_service.reorder_photos(db, user.id, album_id, order)


# ── Standalone photo endpoints ─────────────────────────────────────────────────

@photos_router.post("/{photo_id}/confirm", response_model=PhotoResponse)
def confirm_upload(
    photo_id: int,
    data:     PhotoConfirmRequest,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    """Step 2: Confirm the upload to R2 was successful."""
    return photo_service.confirm_photo_upload(db, user.id, photo_id, data)


@photos_router.patch("/{photo_id}", response_model=PhotoResponse)
def update_photo(
    photo_id: int,
    data:     PhotoUpdate,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    return photo_service.update_photo(db, user.id, photo_id, data)


@photos_router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: int,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    photo_service.delete_photo(db, user.id, photo_id)


@photos_router.post("/{photo_id}/favorite", response_model=PhotoResponse)
def toggle_favorite(
    photo_id: int,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    return photo_service.toggle_favorite(db, user.id, photo_id)


router.include_router(trips_router)
router.include_router(albums_router)
router.include_router(photos_router)