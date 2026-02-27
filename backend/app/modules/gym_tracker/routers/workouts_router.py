from ..services import workout_service
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..schemas import WorkoutCreate, WorkoutResponse, WorkoutEnd, WorkoutDetailResponse
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from typing import List

router = APIRouter(prefix="/workouts", tags=["Workouts"])

@router.get("/", response_model=List[WorkoutResponse])
def get_workouts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return workout_service.get_all(db, user_id=user.id)

@router.get("/{workout_id}/long", response_model=WorkoutDetailResponse)
def get_workouts_long(
    workout_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return workout_service.get_by_id_with_details(db, workout_id, user_id=user.id)

@router.get('/{workout_id}', response_model=WorkoutResponse)
def get_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return workout_service.get_by_id(db, workout_id, user_id=user.id)

@router.post("/", response_model=WorkoutResponse, status_code=201)
def start_workout(
    data: WorkoutCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return workout_service.start_workout(db, data, user_id=user.id)

@router.post("/{workout_id}", response_model=WorkoutResponse, status_code=201)
def end_workout(
    workout_id: int,
    data: WorkoutEnd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return workout_service.end_workout(db, workout_id, data, user_id=user.id)

@router.delete("/{workout_id}", response_description='Successfully deleted', status_code=204)
def delete_workout(
    workout_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    workout_service.delete_workout(db, workout_id, user_id=user.id)
    return {"message": "Workout eliminated", "id": workout_id}