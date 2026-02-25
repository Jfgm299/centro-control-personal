from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from ...models.gym_track.workout import Workout
from ...models.gym_track.workout_muscle_group import WorkoutMuscleGroup
from ...schemas.gym_track.workout import WorkoutCreate, WorkoutEnd, WorkoutDetailResponse
from ...schemas.gym_track.exercise import ExerciseDetailResponse
from ...schemas.gym_track.set import SetResponse
from ...exceptions import WorkoutAlreadyEndedError, WorkoutNotFoundError, WorkoutAlreadyActiveError


class WorkoutService:

    def start_workout(self, db: Session, data: WorkoutCreate) -> Workout:
        """Iniciar un nuevo workout"""
        active_workout = db.query(Workout).filter(Workout.ended_at == None).first()
        if active_workout:
            raise WorkoutAlreadyActiveError(active_workout.id)

        workout = Workout(notes=data.notes)
        db.add(workout)
        db.flush()

        for muscle_group_str in data.muscle_groups:
            mg = WorkoutMuscleGroup(
                workout_id=workout.id,
                muscle_group=muscle_group_str
            )
            db.add(mg)

        db.commit()
        db.refresh(workout)
        return workout

    def end_workout(self, db: Session, workout_id: int, data: WorkoutEnd) -> Optional[Workout]:
        """Finalizar workout y calcular estadísticas"""
        workout = db.query(Workout).filter(Workout.id == workout_id).first()

        if not workout:
            raise WorkoutNotFoundError(workout_id)
        if workout.ended_at:
            raise WorkoutAlreadyEndedError(workout_id)

        workout.ended_at = datetime.now(timezone.utc)
        duration = (workout.ended_at - workout.started_at).total_seconds()
        workout.duration_minutes = int(duration / 60)
        workout.total_exercises = len(workout.exercises)
        workout.total_sets = sum(len(exercise.sets) for exercise in workout.exercises)

        if data.notes:
            workout.notes = data.notes

        db.commit()
        db.refresh(workout)
        return workout

    def get_by_id(self, db: Session, workout_id: int) -> Optional[dict]:
        """Obtener workout por ID"""
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        if not workout:
            raise WorkoutNotFoundError(workout_id)

        return {
            "id": workout.id,
            "started_at": workout.started_at,
            "ended_at": workout.ended_at,
            "duration_minutes": workout.duration_minutes,
            "total_exercises": workout.total_exercises,
            "total_sets": workout.total_sets,
            "notes": workout.notes,
            "muscle_groups": [mg.muscle_group.value for mg in workout.muscle_groups]
        }

    def get_all(self, db: Session, skip: int = 0, limit: int = 50) -> List[dict]:
        """Listar workouts"""
        workouts = db.query(Workout).offset(skip).limit(limit).all()

        return [
            {
                "id": w.id,
                "started_at": w.started_at,
                "ended_at": w.ended_at,
                "duration_minutes": w.duration_minutes,
                "total_exercises": w.total_exercises,
                "total_sets": w.total_sets,
                "notes": w.notes,
                "muscle_groups": [mg.muscle_group.value for mg in w.muscle_groups]
            }
            for w in workouts
        ]

    def get_by_id_with_details(self, db: Session, workout_id: int) -> Optional[WorkoutDetailResponse]:
        """Obtener workout completo con ejercicios y sets"""
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        if not workout:
            raise WorkoutNotFoundError(workout_id)

        return WorkoutDetailResponse(
            id=workout.id,
            started_at=workout.started_at,
            ended_at=workout.ended_at,
            duration_minutes=workout.duration_minutes,
            total_exercises=workout.total_exercises or 0,
            total_sets=workout.total_sets or 0,
            notes=workout.notes,
            muscle_groups=[mg.muscle_group.value for mg in workout.muscle_groups],
            exercises=[
                ExerciseDetailResponse(
                    id=ex.id,
                    workout_id=ex.workout_id,
                    name=ex.name,
                    exercise_type=ex.exercise_type,  # ← añadido
                    order=ex.order,
                    notes=ex.notes,
                    created_at=ex.created_at,
                    sets=[
                        SetResponse(
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
                        ) for s in ex.sets
                    ]
                ) for ex in workout.exercises
            ]
        )

    def delete_workout(self, db: Session, workout_id: int) -> bool:
        """Eliminar workout"""
        workout_db = db.query(Workout).filter(Workout.id == workout_id).first()
        if not workout_db:
            raise WorkoutNotFoundError(workout_id)

        db.delete(workout_db)
        db.commit()
        return True


workout_service = WorkoutService()