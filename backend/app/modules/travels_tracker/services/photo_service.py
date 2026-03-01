from sqlalchemy.orm import Session
from ..models.photo import Photo
from ..enums.photo_status import PhotoStatus
from ..schemas.photo_schema import (
    PhotoUploadRequest, PhotoConfirmRequest, PhotoUpdate, PhotoReorderItem,
)
from ..exceptions.travel_exceptions import (
    PhotoNotFoundError,
    PhotoAlreadyConfirmedError,
    PhotoNotUploadedToStorageError,
    InvalidContentTypeError,
    TripPhotoLimitReachedError,
)
from .album_service import get_album_by_id
from .storage_service import storage_service

# ── Constants ──────────────────────────────────────────────────────────────────
MAX_PHOTOS_PER_TRIP = 30

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "image/gif",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _count_uploaded_photos_in_trip(db: Session, user_id: int, trip_id: int) -> int:
    """Count only confirmed (uploaded) photos — pending ones don't count toward the limit."""
    return (
        db.query(Photo)
        .filter(
            Photo.trip_id == trip_id,
            Photo.user_id == user_id,
            Photo.status == PhotoStatus.uploaded,
        )
        .count()
    )


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"


# ── Upload flow ────────────────────────────────────────────────────────────────

def request_photo_upload(
    db: Session, user_id: int, album_id: int, data: PhotoUploadRequest
) -> dict:
    """
    Step 1 of the upload flow.
    Validates content_type and trip limit, creates a pending Photo record,
    then returns a presigned PUT URL for the frontend to upload directly to R2.
    """
    if data.content_type not in ALLOWED_CONTENT_TYPES:
        raise InvalidContentTypeError(data.content_type)

    album = get_album_by_id(db, user_id, album_id)

    # Enforce trip photo limit (only uploaded photos count)
    count = _count_uploaded_photos_in_trip(db, user_id, album.trip_id)
    if count >= MAX_PHOTOS_PER_TRIP:
        raise TripPhotoLimitReachedError(album.trip_id, MAX_PHOTOS_PER_TRIP)

    ext = _get_extension(data.filename)

    # Create the pending record first with db.flush() to obtain the auto-generated ID
    # without committing — we need the ID to build the deterministic R2 key.
    photo = Photo(
        album_id=album_id,
        trip_id=album.trip_id,
        user_id=user_id,
        filename=data.filename,
        r2_key="",  # placeholder until we have the ID
        content_type=data.content_type,
        status=PhotoStatus.pending,
    )
    db.add(photo)
    db.flush()  # assigns photo.id without committing the transaction

    key = storage_service.build_photo_key(user_id, album.trip_id, album_id, photo.id, ext)
    photo.r2_key = key
    db.commit()
    db.refresh(photo)

    upload_url = storage_service.generate_upload_url(key, data.content_type)

    return {
        "photo_id":   photo.id,
        "upload_url": upload_url,
        "r2_key":     key,
        "expires_in": 600,
    }


def confirm_photo_upload(
    db: Session, user_id: int, photo_id: int, data: PhotoConfirmRequest
) -> Photo:
    """
    Step 2 of the upload flow.
    Verifies the object actually landed in R2, then marks the photo as uploaded.
    """
    photo = db.query(Photo).filter(Photo.id == photo_id, Photo.user_id == user_id).first()
    if not photo:
        raise PhotoNotFoundError(photo_id)
    if photo.status == PhotoStatus.uploaded:
        raise PhotoAlreadyConfirmedError(photo_id)
    if not storage_service.object_exists(photo.r2_key):
        raise PhotoNotUploadedToStorageError(photo_id)

    photo.status     = PhotoStatus.uploaded
    photo.public_url = storage_service.build_public_url(photo.r2_key)
    photo.size_bytes = data.size_bytes
    photo.width      = data.width
    photo.height     = data.height
    photo.taken_at   = data.taken_at
    db.commit()
    db.refresh(photo)
    return photo


# ── CRUD ───────────────────────────────────────────────────────────────────────

def get_photos(db: Session, user_id: int, album_id: int) -> list[Photo]:
    """Returns only confirmed (uploaded) photos, ordered by position then created_at."""
    get_album_by_id(db, user_id, album_id)
    return (
        db.query(Photo)
        .filter(
            Photo.album_id == album_id,
            Photo.user_id == user_id,
            Photo.status == PhotoStatus.uploaded,
        )
        .order_by(Photo.position.asc(), Photo.created_at.asc())
        .all()
    )


def get_photo_by_id(db: Session, user_id: int, photo_id: int) -> Photo:
    photo = (
        db.query(Photo)
        .filter(
            Photo.id == photo_id,
            Photo.user_id == user_id,
            Photo.status == PhotoStatus.uploaded,
        )
        .first()
    )
    if not photo:
        raise PhotoNotFoundError(photo_id)
    return photo


def update_photo(db: Session, user_id: int, photo_id: int, data: PhotoUpdate) -> Photo:
    photo = get_photo_by_id(db, user_id, photo_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(photo, field, value)
    db.commit()
    db.refresh(photo)
    return photo


def delete_photo(db: Session, user_id: int, photo_id: int) -> None:
    photo = get_photo_by_id(db, user_id, photo_id)
    storage_service.delete_object(photo.r2_key)
    db.delete(photo)
    db.commit()


def toggle_favorite(db: Session, user_id: int, photo_id: int) -> Photo:
    photo = get_photo_by_id(db, user_id, photo_id)
    photo.is_favorite = not photo.is_favorite
    db.commit()
    db.refresh(photo)
    return photo


def get_favorites(db: Session, user_id: int) -> list[Photo]:
    """Global favorites collection — all trips."""
    return (
        db.query(Photo)
        .filter(
            Photo.user_id == user_id,
            Photo.is_favorite.is_(True),
            Photo.status == PhotoStatus.uploaded,
        )
        .order_by(Photo.updated_at.desc())
        .all()
    )


def reorder_photos(
    db: Session, user_id: int, album_id: int, order: list[PhotoReorderItem]
) -> list[Photo]:
    get_album_by_id(db, user_id, album_id)
    for item in order:
        db.query(Photo).filter(
            Photo.id == item.photo_id,
            Photo.user_id == user_id,
            Photo.album_id == album_id,
        ).update({"position": item.position})
    db.commit()
    return get_photos(db, user_id, album_id)


def get_trip_photo_count(db: Session, user_id: int, trip_id: int) -> int:
    return _count_uploaded_photos_in_trip(db, user_id, trip_id)