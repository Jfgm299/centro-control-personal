from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from ..models.workout import Workout
from ..models.workout_muscle_group import WorkoutMuscleGroup
from ..schemas import WorkoutCreate, WorkoutEnd, WorkoutDetailResponse
from ..schemas import ExerciseDetailResponse, SetResponse
from ..exceptions import WorkoutAlreadyEndedError, WorkoutNotFoundError, WorkoutAlreadyActiveError


class WorkoutService:

    def _workout_to_dict(self, workout: Workout) -> dict:
        return {
            "id":               workout.id,
            "started_at":       workout.started_at,
            "ended_at":         workout.ended_at,
            "duration_minutes": workout.duration_minutes,
            "total_exercises":  workout.total_exercises,
            "total_sets":       workout.total_sets,
            "notes":            workout.notes,
            "muscle_groups":    [mg.muscle_group.value for mg in workout.muscle_groups],
        }

    def start_workout(self, db: Session, data: WorkoutCreate, user_id: int) -> dict:
        active_workout = db.query(Workout).filter(
            Workout.ended_at == None,
            Workout.user_id == user_id
        ).first()
        if active_workout:
            raise WorkoutAlreadyActiveError(active_workout.id)

        workout = Workout(notes=data.notes, user_id=user_id)
        db.add(workout)
        db.commit()
        db.refresh(workout)
        return self._workout_to_dict(workout)

    def end_workout(self, db: Session, workout_id: int, data: WorkoutEnd, user_id: int) -> dict:
        workout = db.query(Workout).filter(
            Workout.id == workout_id,
            Workout.user_id == user_id
        ).first()
        if not workout:
            raise WorkoutNotFoundError(workout_id)
        if workout.ended_at:
            raise WorkoutAlreadyEndedError(workout_id)

        now = datetime.now(timezone.utc)
        workout.ended_at = now

        started_at = workout.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        duration = (now - started_at).total_seconds()
        workout.duration_minutes = int(duration / 60)
        workout.total_exercises  = len(workout.exercises)
        workout.total_sets       = sum(len(ex.sets) for ex in workout.exercises)

        if data.notes:
            workout.notes = data.notes

        # ── Auto-compute muscle groups from exercises ─────────────────────────
        # Eliminar los existentes (por si acaso) y recomputar
        for mg in list(workout.muscle_groups):
            db.delete(mg)
        db.flush()

        seen = set()
        for ex in workout.exercises:
            for group in (ex.muscle_groups or []):
                if group not in seen:
                    seen.add(group)
                    db.add(WorkoutMuscleGroup(workout_id=workout.id, muscle_group=group))

        db.commit()
        db.refresh(workout)
        return self._workout_to_dict(workout)

    def get_by_id(self, db: Session, workout_id: int, user_id: int) -> dict:
        workout = db.query(Workout).filter(
            Workout.id == workout_id,
            Workout.user_id == user_id
        ).first()
        if not workout:
            raise WorkoutNotFoundError(workout_id)
        return self._workout_to_dict(workout)

    def get_all(self, db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[dict]:
        workouts = db.query(Workout).filter(
            Workout.user_id == user_id
        ).order_by(Workout.started_at.desc()).offset(skip).limit(limit).all()
        return [self._workout_to_dict(w) for w in workouts]

    def get_by_id_with_details(self, db: Session, workout_id: int, user_id: int) -> WorkoutDetailResponse:
        workout = db.query(Workout).filter(
            Workout.id == workout_id,
            Workout.user_id == user_id
        ).first()
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
                    exercise_type=ex.exercise_type,
                    muscle_groups=ex.muscle_groups or [],
                    catalog_id=ex.catalog_id,
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
                            created_at=s.created_at,
                        ) for s in ex.sets
                    ]
                ) for ex in workout.exercises
            ]
        )

    def delete_workout(self, db: Session, workout_id: int, user_id: int) -> bool:
        workout_db = db.query(Workout).filter(
            Workout.id == workout_id,
            Workout.user_id == user_id
        ).first()
        if not workout_db:
            raise WorkoutNotFoundError(workout_id)
        db.delete(workout_db)
        db.commit()
        return True


workout_service = WorkoutService()