# routers/gym_track/workouts.py
from ...services import workout_service
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from ...schemas import WorkoutCreate, WorkoutResponse, WorkoutEnd, WorkoutDetailResponse, ExerciseResponse
from ...database import get_db
from typing import List

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.get("/", response_model=List[WorkoutResponse])
def get_workouts(
    db: Session = Depends(get_db)
):
    return workout_service.get_all(db)

@router.get("/{workout_id}/long", response_model=WorkoutDetailResponse)
def get_workouts_long(
    workout_id: int,
    db: Session = Depends(get_db)
    
):
    return workout_service.get_by_id_with_details(db, workout_id)

@router.get('/{workout_id}', response_model=WorkoutResponse)
def get_workout(
    workout_id:int,
    db: Session = Depends(get_db)
):
    workout_db = workout_service.get_by_id(db,workout_id)
    return workout_db

@router.post("/", response_model=WorkoutResponse, status_code=201)
def start_workout(data: WorkoutCreate, db: Session = Depends(get_db)):
    return workout_service.start_workout(db, data)

@router.post("/{workout_id}", response_model=WorkoutResponse, status_code=201)
def end_workout(
    workout_id:int,
    data: WorkoutEnd,
    db: Session = Depends(get_db)
):
    workout_db = workout_service.end_workout(db, workout_id, data)
    return workout_db

@router.delete("/{workout_id}", response_description='Successfully deleted', status_code=204)
def delete_workout(
    workout_id:int,
    db: Session = Depends(get_db)
):
    sucess = workout_service.delete_workout(db, workout_id)
    return {"message": "Workout eliminated", "id": workout_id}
