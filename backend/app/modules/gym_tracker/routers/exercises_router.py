
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..schemas import ExerciseResponse
from app.core.database import get_db
from typing import List

from ..services import exercise_service
from ..schemas import ExerciseCreate, ExerciseResponse, ExerciseDetailResponse

router = APIRouter(prefix="/workouts", tags=["exercises"])


@router.post(
    "/{workout_id}/exercises", 
    response_model=ExerciseResponse, 
    status_code=201,
    tags=['exercises']
)
def add_exercise_to_workout(
    workout_id: int,
    data: ExerciseCreate,
    db: Session = Depends(get_db)
):
    """Add an exercise to the workout"""
    return exercise_service.create(db, workout_id, data)


@router.get(
    "/{workout_id}/exercises",
    response_model=List[ExerciseResponse],
    tags=['exercises']
)
def get_workout_exercises(
    workout_id: int,
    db: Session = Depends(get_db)
):
    """List all exercises of a workout"""
    return exercise_service.get_all_by_workout(db, workout_id)

@router.get('/{workout_id}/{exercise_id}', response_model=ExerciseResponse, tags=['exercises'])
def get_exercise(
    workout_id: int,
    exercise_id: int,
    db: Session = Depends(get_db)
):
    return exercise_service.get_exercise_by_id(db, workout_id, exercise_id)

@router.get("/{workout_id}/{exercise_id}/long", response_model=ExerciseDetailResponse, tags=['exercises'])
def get_exercise_detail(
    workout_id: int,
    exercise_id: int,
    db: Session = Depends(get_db)
):
    """Obtain details of a exercise"""
    return exercise_service.get_exercise_by_id_with_details(db, workout_id, exercise_id)

@router.delete('/{workout_id}/{exercise_id}', response_description='Successfully deleted', status_code=204)
def delete_exercise(
    workout_id: int,
    exercise_id: int,
    db: Session = Depends(get_db)
):
    '''Remove an exercise from a workout'''
    success = exercise_service.delete_exercise(db,workout_id, exercise_id)
    return {"message": "Exercise eliminated", "id": exercise_id}
