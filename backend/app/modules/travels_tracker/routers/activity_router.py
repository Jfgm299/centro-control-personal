from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from ..schemas.activity_schema import ActivityCreate, ActivityUpdate, ActivityResponse
from ..services import activity_service

router = APIRouter(prefix="/travels/trips/{trip_id}/activities", tags=["Travels"])


@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    trip_id: int,
    data:    ActivityCreate,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    return activity_service.create_activity(db, user.id, trip_id, data)


@router.get("/", response_model=list[ActivityResponse])
def get_activities(
    trip_id: int,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    return activity_service.get_activities(db, user.id, trip_id)


@router.patch("/{activity_id}", response_model=ActivityResponse)
def update_activity(
    trip_id:     int,
    activity_id: int,
    data:        ActivityUpdate,
    db:          Session = Depends(get_db),
    user:        User    = Depends(get_current_user),
):
    return activity_service.update_activity(db, user.id, activity_id, data)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    trip_id:     int,
    activity_id: int,
    db:          Session = Depends(get_db),
    user:        User    = Depends(get_current_user),
):
    activity_service.delete_activity(db, user.id, activity_id)