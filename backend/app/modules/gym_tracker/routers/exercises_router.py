from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from typing import List
from ..services import exercise_service
from ..schemas import ExerciseCreate, ExerciseResponse, ExerciseDetailResponse

router = APIRouter(prefix="/workouts", tags=['Exercises'])


@router.post("/{workout_id}/exercises", response_model=ExerciseResponse, status_code=201)
def add_exercise_to_workout(
    workout_id: int,
    data: ExerciseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return exercise_service.create(db, workout_id, data, user_id=user.id)


@router.get("/{workout_id}/exercises", response_model=List[ExerciseResponse])
def get_workout_exercises(
    workout_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return exercise_service.get_all_by_workout(db, workout_id, user_id=user.id)


@router.get("/{workout_id}/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(
    workout_id: int,
    exercise_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return exercise_service.get_exercise_by_id(db, workout_id, exercise_id, user_id=user.id)


@router.get("/{workout_id}/{exercise_id}/long", response_model=ExerciseDetailResponse)
def get_exercise_detail(
    workout_id: int,
    exercise_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return exercise_service.get_exercise_by_id_with_details(db, workout_id, exercise_id, user_id=user.id)


@router.delete("/{workout_id}/{exercise_id}", status_code=204)
def delete_exercise(
    workout_id: int,
    exercise_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    exercise_service.delete_exercise(db, workout_id, exercise_id, user_id=user.id)