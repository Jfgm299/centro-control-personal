from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from ..schemas.album_schema import AlbumCreate, AlbumUpdate, AlbumReorderItem, AlbumResponse
from ..services import album_service

# Two routers: trip-nested for creation/listing, standalone for direct album access
trip_albums_router = APIRouter(prefix="/travels/trips/{trip_id}/albums", tags=["Travels"])
albums_router      = APIRouter(prefix="/travels/albums", tags=["Travels"])

# ── Combine into a single exportable router ────────────────────────────────────
router = APIRouter()


# ── CRITICAL ORDER: /reorder BEFORE /{album_id} ───────────────────────────────

@trip_albums_router.post("/reorder", response_model=list[AlbumResponse])
def reorder_albums(
    trip_id: int,
    order:   list[AlbumReorderItem],
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    return album_service.reorder_albums(db, user.id, trip_id, order)


@trip_albums_router.post("/", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
def create_album(
    trip_id: int,
    data:    AlbumCreate,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    return album_service.create_album(db, user.id, trip_id, data)


@trip_albums_router.get("/", response_model=list[AlbumResponse])
def get_albums(
    trip_id: int,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    return album_service.get_albums(db, user.id, trip_id)


@albums_router.get("/{album_id}", response_model=AlbumResponse)
def get_album(
    album_id: int,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    return album_service.get_album_by_id(db, user.id, album_id)


@albums_router.patch("/{album_id}", response_model=AlbumResponse)
def update_album(
    album_id: int,
    data:     AlbumUpdate,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    return album_service.update_album(db, user.id, album_id, data)


@albums_router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(
    album_id: int,
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    album_service.delete_album(db, user.id, album_id)


@albums_router.post("/{album_id}/cover", response_model=AlbumResponse)
def set_album_cover(
    album_id: int,
    photo_id: int = Query(..., description="ID of the photo to set as album cover"),
    db:       Session = Depends(get_db),
    user:     User    = Depends(get_current_user),
):
    return album_service.set_album_cover(db, user.id, album_id, photo_id)


router.include_router(trip_albums_router)
router.include_router(albums_router)