from sqlalchemy.orm import Session
from ..models.album import Album
from ..models.photo import Photo
from ..enums.photo_status import PhotoStatus
from ..schemas.album_schema import AlbumCreate, AlbumUpdate, AlbumReorderItem
from ..exceptions.travel_exceptions import AlbumNotFoundError, PhotoNotFoundError
from .trip_service import get_trip_by_id
from .storage_service import storage_service


def create_album(db: Session, user_id: int, trip_id: int, data: AlbumCreate) -> Album:
    get_trip_by_id(db, user_id, trip_id)  # verifies ownership
    album = Album(user_id=user_id, trip_id=trip_id, **data.model_dump())
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


def get_albums(db: Session, user_id: int, trip_id: int) -> list[Album]:
    get_trip_by_id(db, user_id, trip_id)
    return (
        db.query(Album)
        .filter(Album.trip_id == trip_id, Album.user_id == user_id)
        .order_by(Album.position.asc(), Album.created_at.asc())
        .all()
    )


def get_album_by_id(db: Session, user_id: int, album_id: int) -> Album:
    album = db.query(Album).filter(Album.id == album_id, Album.user_id == user_id).first()
    if not album:
        raise AlbumNotFoundError(album_id)
    return album


def update_album(db: Session, user_id: int, album_id: int, data: AlbumUpdate) -> Album:
    album = get_album_by_id(db, user_id, album_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(album, field, value)
    db.commit()
    db.refresh(album)
    return album


def delete_album(db: Session, user_id: int, album_id: int) -> None:
    album = get_album_by_id(db, user_id, album_id)
    storage_service.delete_objects_by_prefix(
        storage_service.build_album_prefix(user_id, album.trip_id, album_id)
    )
    db.delete(album)
    db.commit()


def reorder_albums(
    db: Session, user_id: int, trip_id: int, order: list[AlbumReorderItem]
) -> list[Album]:
    get_trip_by_id(db, user_id, trip_id)
    for item in order:
        db.query(Album).filter(
            Album.id == item.album_id,
            Album.user_id == user_id,
            Album.trip_id == trip_id,
        ).update({"position": item.position})
    db.commit()
    return get_albums(db, user_id, trip_id)


def set_album_cover(db: Session, user_id: int, album_id: int, photo_id: int) -> Album:
    album = get_album_by_id(db, user_id, album_id)
    photo = (
        db.query(Photo)
        .filter(
            Photo.id == photo_id,
            Photo.user_id == user_id,
            Photo.album_id == album_id,
            Photo.status == PhotoStatus.uploaded,
        )
        .first()
    )
    if not photo:
        raise PhotoNotFoundError(photo_id)
    album.cover_photo_key = photo.r2_key
    album.cover_photo_url = photo.public_url
    db.commit()
    db.refresh(album)
    return album