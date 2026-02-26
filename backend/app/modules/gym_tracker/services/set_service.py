from typing import List
from sqlalchemy.orm import Session
from ..models import Set, Exercise, Workout
from ..enums import GymSetType
from ..schemas import SetCreate, SetResponse
from ..exceptions import (
    WorkoutNotFoundError, ExerciseNotFoundError,
    ExerciseNotInWorkoutError, SetNotFoundError, SetTypeMismatchError
)

class SetService:

    def _validate_workout_and_exercise(self, db: Session, workout_id: int, exercise_id: int):
        """Valida que el workout y ejercicio existen y están relacionados"""
        workout_db = db.query(Workout).filter(Workout.id == workout_id).first()
        if not workout_db:
            raise WorkoutNotFoundError(workout_id)

        exercise_db = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise_db:
            raise ExerciseNotFoundError(exercise_id)

        if exercise_db.workout_id != workout_id:
            raise ExerciseNotInWorkoutError(exercise_id, workout_id)

        return exercise_db

    def create_set(self, db: Session, workout_id: int, exercise_id: int, data: SetCreate) -> SetResponse:
        exercise_db = self._validate_workout_and_exercise(db, workout_id, exercise_id)

        if exercise_db.exercise_type == GymSetType.WEIGHT_REPS:
            if data.weight_kg is None or data.reps is None:
                raise SetTypeMismatchError(exercise_id, exercise_db.exercise_type)

        if exercise_db.exercise_type == GymSetType.CARDIO:
            if data.speed_kmh is None or data.duration_seconds is None:
                raise SetTypeMismatchError(exercise_id, exercise_db.exercise_type)

        last_set = (
            db.query(Set)
            .filter(Set.exercise_id == exercise_id)
            .order_by(Set.set_number.desc())
            .first()
        )
        next_set_number = (last_set.set_number + 1) if last_set else 1

        new_set = Set(
            exercise_id=exercise_id,
            set_number=next_set_number,
            weight_kg=data.weight_kg,
            reps=data.reps,
            speed_kmh=data.speed_kmh,
            incline_percent=data.incline_percent,
            duration_seconds=data.duration_seconds,
            rpe=data.rpe,
            notes=data.notes
        )

        db.add(new_set)
        db.commit()
        db.refresh(new_set)
        return SetResponse.model_validate(new_set)

    def get_sets_by_exercise(self, db: Session, workout_id: int, exercise_id: int) -> List[SetResponse]:
        """Listar todos los sets de un ejercicio"""
        self._validate_workout_and_exercise(db, workout_id, exercise_id)

        sets = (
            db.query(Set)
            .filter(Set.exercise_id == exercise_id)
            .order_by(Set.set_number)
            .all()
        )
        return [SetResponse.model_validate(s) for s in sets]

    def delete_set(self, db: Session, workout_id: int, exercise_id: int, set_id: int) -> bool:
        """Eliminar un set"""
        self._validate_workout_and_exercise(db, workout_id, exercise_id)

        set_db = db.query(Set).filter(
            Set.id == set_id,
            Set.exercise_id == exercise_id
        ).first()

        if not set_db:
            raise SetNotFoundError(set_id)

        db.delete(set_db)
        db.commit()
        return True
    
set_service = SetService()