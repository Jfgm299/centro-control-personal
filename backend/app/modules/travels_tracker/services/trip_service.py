from sqlalchemy.orm import Session
from ..models.trip import Trip
from ..models.photo import Photo
from ..enums.photo_status import PhotoStatus
from ..schemas.trip_schema import TripCreate, TripUpdate
from ..exceptions.travel_exceptions import TripNotFoundError, PhotoNotFoundError
from .storage_service import storage_service


def create_trip(db: Session, user_id: int, data: TripCreate) -> Trip:
    trip = Trip(user_id=user_id, **data.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def get_trips(db: Session, user_id: int) -> list[Trip]:
    return (
        db.query(Trip)
        .filter(Trip.user_id == user_id)
        .order_by(Trip.start_date.desc().nullslast(), Trip.created_at.desc())
        .all()
    )


def get_trip_by_id(db: Session, user_id: int, trip_id: int) -> Trip:
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
    if not trip:
        raise TripNotFoundError(trip_id)
    return trip


def update_trip(db: Session, user_id: int, trip_id: int, data: TripUpdate) -> Trip:
    trip = get_trip_by_id(db, user_id, trip_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(trip, field, value)
    db.commit()
    db.refresh(trip)
    return trip


def delete_trip(db: Session, user_id: int, trip_id: int) -> None:
    trip = get_trip_by_id(db, user_id, trip_id)
    # Remove all R2 objects for this trip before DB delete
    storage_service.delete_objects_by_prefix(
        storage_service.build_trip_prefix(user_id, trip_id)
    )
    db.delete(trip)
    db.commit()


def get_trips_for_map(db: Session, user_id: int) -> list[Trip]:
    """Returns only trips with valid coordinates for the world map."""
    return (
        db.query(Trip)
        .filter(
            Trip.user_id == user_id,
            Trip.lat.isnot(None),
            Trip.lon.isnot(None),
        )
        .order_by(Trip.start_date.desc().nullslast())
        .all()
    )


def set_trip_cover(db: Session, user_id: int, trip_id: int, photo_id: int) -> Trip:
    trip = get_trip_by_id(db, user_id, trip_id)
    photo = (
        db.query(Photo)
        .filter(
            Photo.id == photo_id,
            Photo.user_id == user_id,
            Photo.trip_id == trip_id,
            Photo.status == PhotoStatus.uploaded,
        )
        .first()
    )
    if not photo:
        raise PhotoNotFoundError(photo_id)
    trip.cover_photo_key = photo.r2_key
    trip.cover_photo_url = photo.public_url
    db.commit()
    db.refresh(trip)
    return trip