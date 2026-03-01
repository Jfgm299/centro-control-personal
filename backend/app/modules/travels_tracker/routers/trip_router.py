from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from ..schemas.trip_schema import TripCreate, TripUpdate, TripResponse, TripMapResponse
from ..schemas.photo_schema import PhotoResponse
from ..services import trip_service, photo_service

router = APIRouter(prefix="/travels/trips", tags=["Travels"])


# ── CRITICAL ORDER: literal routes BEFORE /{trip_id} ──────────────────────────

@router.get("/map", response_model=list[TripMapResponse])
def get_trips_map(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Returns all trips with coordinates for the world map."""
    return trip_service.get_trips_for_map(db, user.id)


@router.get("/favorites", response_model=list[PhotoResponse])
def get_favorites(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Returns all favorited photos across all trips."""
    return photo_service.get_favorites(db, user.id)


# ── Standard CRUD ──────────────────────────────────────────────────────────────

@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    data: TripCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return trip_service.create_trip(db, user.id, data)


@router.get("/", response_model=list[TripResponse])
def get_trips(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return trip_service.get_trips(db, user.id)


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: int,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    return trip_service.get_trip_by_id(db, user.id, trip_id)


@router.patch("/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: int,
    data:    TripUpdate,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    return trip_service.update_trip(db, user.id, trip_id, data)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: int,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    trip_service.delete_trip(db, user.id, trip_id)


@router.post("/{trip_id}/cover", response_model=TripResponse)
def set_trip_cover(
    trip_id:  int,
    photo_id: int = Query(..., description="ID of the photo to set as cover"),
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    return trip_service.set_trip_cover(db, user.id, trip_id, photo_id)