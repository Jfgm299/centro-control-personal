from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from ..schemas import SetCreate, SetResponse
from ..services import set_service

router = APIRouter(prefix="/workouts", tags=["Sets"])

@router.post("/{workout_id}/{exercise_id}/sets", response_model=SetResponse, status_code=201, summary="Add Set To Exercise")
def create_set(
    workout_id: int, exercise_id: int, data: SetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return set_service.create_set(db, workout_id, exercise_id, data, user_id=user.id)

@router.get("/{workout_id}/{exercise_id}/sets", response_model=List[SetResponse], summary="Get Exercise Sets")
def get_sets(
    workout_id: int, exercise_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return set_service.get_sets_by_exercise(db, workout_id, exercise_id, user_id=user.id)

@router.delete("/{workout_id}/{exercise_id}/sets/{set_id}", status_code=204, summary="Delete Set")
def delete_set(
    workout_id: int, exercise_id: int, set_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    set_service.delete_set(db, workout_id, exercise_id, set_id, user_id=user.id)