from sqlalchemy.orm import Session
from typing import Optional
from ..models.exercise import Exercise
from ..models.workout import Workout
from ..schemas import ExerciseCreate, ExerciseDetailResponse, SetResponse
from ..exceptions import ExerciseNotFoundError, WorkoutNotFoundError, WorkoutAlreadyEndedError, ExerciseNotInWorkoutError
from app.core.exeptions import NotYoursError

class ExerciseService:

    def _get_workout_for_user(self, db: Session, workout_id: int, user_id: int) -> Workout:
        """Obtiene el workout verificando que pertenece al usuario"""
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        if not workout:
            raise WorkoutNotFoundError(workout_id)
        if workout.user_id != user_id:
            raise NotYoursError("workout")
        return workout

    def create(self, db: Session, workout_id: int, data: ExerciseCreate, user_id: int) -> Exercise:
        workout = self._get_workout_for_user(db, workout_id, user_id)
        if workout.ended_at:
            raise WorkoutAlreadyEndedError(workout_id)
        current_count = db.query(Exercise).filter(Exercise.workout_id == workout_id).count()
        normalized_name = data.name.strip().title()
        new_exercise = Exercise(
            workout_id=workout_id,
            name=normalized_name,
            exercise_type=data.exercise_type,
            order=current_count + 1,
            notes=data.notes
        )
        db.add(new_exercise)
        db.commit()
        db.refresh(new_exercise)
        return new_exercise

    def get_by_id(self, db: Session, exercise_id: int, user_id: int) -> Exercise:
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise ExerciseNotFoundError(exercise_id)
        self._get_workout_for_user(db, exercise.workout_id, user_id)
        return exercise

    def get_all_by_workout(self, db: Session, workout_id: int, user_id: int) -> list[Exercise]:
        self._get_workout_for_user(db, workout_id, user_id)
        return db.query(Exercise).filter(
            Exercise.workout_id == workout_id
        ).order_by(Exercise.order).all()

    def get_exercise_by_id(self, db: Session, workout_id: int, exercise_id: int, user_id: int) -> Exercise:
        self._get_workout_for_user(db, workout_id, user_id)
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise ExerciseNotFoundError(exercise_id)
        if exercise.workout_id != workout_id:
            raise ExerciseNotInWorkoutError(exercise_id, workout_id)
        return exercise

    def get_exercise_by_id_with_details(self, db: Session, workout_id: int, exercise_id: int, user_id: int) -> Optional[ExerciseDetailResponse]:
        self._get_workout_for_user(db, workout_id, user_id)
        exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise ExerciseNotFoundError(exercise_id)
        if exercise.workout_id != workout_id:
            raise ExerciseNotInWorkoutError(exercise_id, workout_id)
        return ExerciseDetailResponse(
            id=exercise.id,
            workout_id=exercise.workout_id,
            name=exercise.name,
            exercise_type=exercise.exercise_type,
            order=exercise.order,
            notes=exercise.notes,
            created_at=exercise.created_at,
            sets=[SetResponse(
                id=s.id,
                exercise_id=s.exercise_id,
                set_number=s.set_number,
                weight_kg=s.weight_kg,
                reps=s.reps,
                speed_kmh=s.speed_kmh,
                incline_percent=s.incline_percent,
                duration_seconds=s.duration_seconds,
                rpe=s.rpe,
                notes=s.notes,
                created_at=s.created_at
            ) for s in exercise.sets]
        )

    def delete_exercise(self, db: Session, workout_id: int, exercise_id: int, user_id: int) -> bool:
        self._get_workout_for_user(db, workout_id, user_id)
        exercise_db = db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise_db:
            raise ExerciseNotFoundError(exercise_id)
        if exercise_db.workout_id != workout_id:
            raise ExerciseNotInWorkoutError(exercise_id, workout_id)
        db.delete(exercise_db)
        db.commit()
        return True

exercise_service = ExerciseService()