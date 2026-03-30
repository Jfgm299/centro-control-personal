"""
Handlers de automatizaciones para gym_tracker.
Contrato: handler(payload, config, db, user_id) -> dict

TRIGGERS:
    handle_workout_started              — Workout iniciado
    handle_workout_ended                — Workout terminado
    handle_personal_record_weight       — Récord personal de peso
    handle_body_measurement_recorded    — Medición corporal registrada
    handle_workout_inactivity           — N días sin entrenar

ACCIONES:
    action_get_last_workout_summary     — Resumen del último workout
    action_get_weekly_stats             — Estadísticas semanales
    action_get_exercise_progression     — Progresión de un ejercicio
    action_get_body_measurement_trend   — Tendencia de mediciones corporales
"""
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models.workout import Workout
from .models.exercise import Exercise
from .models.set import Set
from .models.body_measurement import BodyMeasurement
from .enums import GymSetType


# ── Utilidades internas ───────────────────────────────────────────────────────

def _workout_to_dict(workout: Workout) -> dict:
    return {
        "id":               workout.id,
        "started_at":       workout.started_at.isoformat() if workout.started_at else None,
        "ended_at":         workout.ended_at.isoformat() if workout.ended_at else None,
        "duration_minutes": workout.duration_minutes,
        "total_exercises":  workout.total_exercises,
        "total_sets":       workout.total_sets,
        "notes":            workout.notes,
        "muscle_groups":    [mg.muscle_group.value for mg in workout.muscle_groups],
    }


def _measurement_to_dict(m: BodyMeasurement) -> dict:
    return {
        "id":                  m.id,
        "recorded_at":         m.created_at.isoformat() if m.created_at else None,
        "weight_kg":           m.weight_kg,
        "body_fat_percentage": m.body_fat_percentage,
    }


# ── TRIGGER HANDLERS ──────────────────────────────────────────────────────────

def handle_workout_started(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando se inicia un workout.
    Payload: {"workout_id": int, "started_at": str}
    Config:  {"day_of_week": str (optional)}
    """
    workout_id = payload.get("workout_id")
    started_at = payload.get("started_at")

    if not workout_id:
        return {"matched": False, "reason": "no workout_id in payload"}
    if not started_at:
        return {"matched": False, "reason": "no started_at in payload"}

    # Filtro: day_of_week
    day_of_week = config.get("day_of_week")
    if day_of_week:
        DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if day_of_week in DAYS:
            today_idx = datetime.now(timezone.utc).weekday()  # 0=lunes
            if DAYS[today_idx] != day_of_week:
                return {"matched": False, "reason": "day_of_week filter not matched"}
        # valor inválido → no filtrar (fall through)

    workout = db.query(Workout).filter(
        Workout.id == workout_id,
        Workout.user_id == user_id,
    ).first()
    if not workout:
        return {"matched": False, "reason": f"workout {workout_id} not found"}

    return {"matched": True, "workout_id": workout_id, "started_at": started_at}


def handle_workout_ended(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando se termina un workout.
    Payload: {"workout_id": int, "duration_minutes": int|None, "total_exercises": int,
              "total_sets": int, "muscle_groups": list[str]}
    Config:  {min_duration_minutes, max_duration_minutes, min_exercises, min_sets,
              required_muscle_groups: list[str]}
    """
    workout_id = payload.get("workout_id")
    if not workout_id:
        return {"matched": False, "reason": "no workout_id in payload"}

    duration    = payload.get("duration_minutes")
    total_ex    = payload.get("total_exercises", 0)
    total_sets  = payload.get("total_sets", 0)
    muscle_grps = payload.get("muscle_groups", [])

    # Validar consistencia de config
    min_dur = config.get("min_duration_minutes")
    max_dur = config.get("max_duration_minutes")
    if min_dur is not None and max_dur is not None and min_dur > max_dur:
        return {"matched": False, "reason": "invalid config: min_duration_minutes > max_duration_minutes"}

    # Filtro: min_duration_minutes
    if min_dur is not None:
        if duration is None:
            return {"matched": False, "reason": "duration_minutes unavailable"}
        if duration < min_dur:
            return {"matched": False, "reason": f"duration {duration} min below minimum {min_dur} min"}

    # Filtro: max_duration_minutes
    if max_dur is not None:
        if duration is None:
            return {"matched": False, "reason": "duration_minutes unavailable"}
        if duration > max_dur:
            return {"matched": False, "reason": f"duration {duration} min above maximum {max_dur} min"}

    # Filtro: min_exercises
    min_ex = config.get("min_exercises")
    if min_ex is not None and total_ex < min_ex:
        return {"matched": False, "reason": f"total_exercises {total_ex} below minimum {min_ex}"}

    # Filtro: min_sets
    min_s = config.get("min_sets")
    if min_s is not None and total_sets < min_s:
        return {"matched": False, "reason": f"total_sets {total_sets} below minimum {min_s}"}

    # Filtro: required_muscle_groups (strings — el modelo usa enum values)
    req_groups = config.get("required_muscle_groups")
    if req_groups:
        valid_req = [g for g in req_groups if isinstance(g, str)]
        missing = [g for g in valid_req if g not in muscle_grps]
        if missing:
            return {"matched": False, "reason": f"missing required muscle groups: {missing}"}

    workout = db.query(Workout).filter(
        Workout.id == workout_id,
        Workout.user_id == user_id,
    ).first()
    if not workout:
        return {"matched": False, "reason": f"workout {workout_id} not found"}

    return {"matched": True, "workout": _workout_to_dict(workout)}


def handle_personal_record_weight(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando se establece un récord personal de peso.
    Payload: {"exercise_name": str, "new_weight_kg": float, "previous_record_kg": float|None,
              "reps": int|None, "workout_id": int, "set_id": int}
    Config:  {"exercise_name": str (opt), "min_weight_kg": int (opt)}
    """
    exercise_name   = payload.get("exercise_name")
    new_weight_kg   = payload.get("new_weight_kg")
    previous_record = payload.get("previous_record_kg")

    if not exercise_name:
        return {"matched": False, "reason": "missing required payload field: exercise_name"}
    if new_weight_kg is None:
        return {"matched": False, "reason": "missing required payload field: new_weight_kg"}
    if new_weight_kg <= 0:
        return {"matched": False, "reason": "weight_kg must be > 0"}

    # Filtro: exercise_name (case-insensitive)
    filter_ex = config.get("exercise_name")
    if filter_ex and filter_ex.lower() != exercise_name.lower():
        return {"matched": False, "reason": "exercise_name filter not matched"}

    # Filtro: min_weight_kg
    min_w = config.get("min_weight_kg")
    if min_w is not None and new_weight_kg < min_w:
        return {"matched": False, "reason": f"new_weight_kg {new_weight_kg} below min_weight_kg {min_w}"}

    return {
        "matched":            True,
        "exercise_name":      exercise_name,
        "new_weight_kg":      new_weight_kg,
        "previous_record_kg": previous_record,
        "reps":               payload.get("reps"),
        "workout_id":         payload.get("workout_id"),
        "set_id":             payload.get("set_id"),
    }


def handle_body_measurement_recorded(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando se registra una medición corporal.
    Payload: {"measurement_id": int, "weight_kg": float|None, "body_fat_percentage": float|None,
              "recorded_at": str}
    Config:  {"min_weight_kg": int (opt), "max_weight_kg": int (opt), "require_body_fat": bool (opt)}
    """
    measurement_id = payload.get("measurement_id")
    if not measurement_id:
        return {"matched": False, "reason": "no measurement_id in payload"}

    weight_kg = payload.get("weight_kg")
    body_fat  = payload.get("body_fat_percentage")

    # Validar consistencia de config
    min_w = config.get("min_weight_kg")
    max_w = config.get("max_weight_kg")
    if min_w is not None and max_w is not None and min_w > max_w:
        return {"matched": False, "reason": "invalid config: min_weight_kg > max_weight_kg"}

    # Filtro: min_weight_kg
    if min_w is not None:
        if weight_kg is None:
            return {"matched": False, "reason": "weight_kg not available for comparison"}
        if weight_kg < min_w:
            return {"matched": False, "reason": f"weight_kg {weight_kg} below min_weight_kg {min_w}"}

    # Filtro: max_weight_kg
    if max_w is not None:
        if weight_kg is None:
            return {"matched": False, "reason": "weight_kg not available for comparison"}
        if weight_kg > max_w:
            return {"matched": False, "reason": f"weight_kg {weight_kg} above max_weight_kg {max_w}"}

    # Filtro: require_body_fat
    if config.get("require_body_fat") and body_fat is None:
        return {"matched": False, "reason": "body_fat_percentage required but not present"}

    m = db.query(BodyMeasurement).filter(
        BodyMeasurement.id == measurement_id,
        BodyMeasurement.user_id == user_id,
    ).first()
    if not m:
        return {"matched": False, "reason": f"measurement {measurement_id} not found"}

    return {
        "matched":             True,
        "measurement_id":      measurement_id,
        "weight_kg":           weight_kg,
        "body_fat_percentage": body_fat,
        "recorded_at":         payload.get("recorded_at"),
    }


def handle_workout_inactivity(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando el usuario lleva N días sin entrenar.
    Payload: {"days_since_last_workout": int|None, "last_workout_date": str|None}
    Config:  {"days_without_workout": int (required)}
    """
    days_since    = payload.get("days_since_last_workout")
    last_date_str = payload.get("last_workout_date")

    threshold = config.get("days_without_workout")
    if threshold is None or not isinstance(threshold, int):
        return {"matched": False, "reason": "days_without_workout missing or invalid"}
    if threshold < 1:
        return {"matched": False, "reason": "days_without_workout must be >= 1"}

    # Usuario que nunca ha entrenado
    if days_since is None:
        return {
            "matched":                 True,
            "days_since_last_workout": None,
            "last_workout_date":       None,
            "threshold":               threshold,
            "reason":                  "no workouts ever recorded",
        }

    if days_since >= threshold:
        return {
            "matched":                 True,
            "days_since_last_workout": days_since,
            "last_workout_date":       last_date_str,
            "threshold":               threshold,
        }

    return {
        "matched": False,
        "reason":  f"only {days_since} days since last workout, threshold is {threshold}",
    }


# ── ACTION HANDLERS ───────────────────────────────────────────────────────────

def action_get_last_workout_summary(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: resumen del último workout terminado (o uno específico).
    Config: {"workout_id": int (optional)}
    """
    workout_id = config.get("workout_id")

    if workout_id:
        workout = db.query(Workout).filter(
            Workout.id == workout_id,
            Workout.user_id == user_id,
        ).first()
        if not workout:
            return {"done": False, "reason": f"workout {workout_id} not found"}
    else:
        workout = db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.ended_at.isnot(None),
        ).order_by(Workout.ended_at.desc()).first()
        if not workout:
            return {"done": False, "reason": "no completed workouts found for user"}

    return {"done": True, "workout": _workout_to_dict(workout)}


def action_get_weekly_stats(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: estadísticas de una semana (lun-dom).
    Config: {"week_offset": int (default 0 = semana actual, -1 = anterior)}
    """
    week_offset = config.get("week_offset", 0)
    if not isinstance(week_offset, int):
        week_offset = 0

    today = date.today()
    current_monday = today - timedelta(days=today.weekday())
    target_monday  = current_monday + timedelta(weeks=week_offset)
    target_sunday  = target_monday + timedelta(days=6)

    week_start_dt = datetime(
        target_monday.year, target_monday.month, target_monday.day,
        tzinfo=timezone.utc,
    )
    week_end_dt = datetime(
        target_sunday.year, target_sunday.month, target_sunday.day,
        23, 59, 59, tzinfo=timezone.utc,
    )

    workouts = db.query(Workout).filter(
        Workout.user_id    == user_id,
        Workout.started_at >= week_start_dt,
        Workout.started_at <= week_end_dt,
    ).all()

    total_exercises = sum(w.total_exercises or 0 for w in workouts)
    total_sets      = sum(w.total_sets or 0 for w in workouts)
    muscle_groups   = list({mg.muscle_group.value for w in workouts for mg in w.muscle_groups})
    workout_ids     = [w.id for w in workouts]

    return {
        "done": True,
        "stats": {
            "week_start":      target_monday.isoformat(),
            "week_end":        target_sunday.isoformat(),
            "total_workouts":  len(workouts),
            "total_exercises": total_exercises,
            "total_sets":      total_sets,
            "muscle_groups":   muscle_groups,
            "workout_ids":     workout_ids,
        },
    }


def action_get_exercise_progression(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: progresión de un ejercicio por sesión.
    Config: {"exercise_name": str (required), "limit": int (default 10)}
    """
    exercise_name = config.get("exercise_name")
    if not exercise_name:
        return {"done": False, "reason": "exercise_name is required"}

    limit = config.get("limit", 10)
    if not isinstance(limit, int) or limit < 1:
        limit = 10
    if limit > 100:
        limit = 100

    # N workouts más recientes donde aparece este ejercicio (case-insensitive)
    matching_workouts = (
        db.query(Workout)
        .join(Exercise, Exercise.workout_id == Workout.id)
        .filter(
            Workout.user_id == user_id,
            func.lower(Exercise.name) == exercise_name.lower(),
        )
        .order_by(Workout.started_at.desc())
        .limit(limit)
        .all()
    )

    if not matching_workouts:
        return {"done": False, "reason": f"no sets found for exercise '{exercise_name}'"}

    progression = []
    for workout in reversed(matching_workouts):  # orden ascendente para trend
        sets = (
            db.query(Set)
            .join(Exercise, Set.exercise_id == Exercise.id)
            .filter(
                Exercise.workout_id == workout.id,
                func.lower(Exercise.name) == exercise_name.lower(),
            )
            .all()
        )
        weight_values = [s.weight_kg for s in sets if s.weight_kg is not None]
        reps_values   = [s.reps for s in sets if s.reps is not None]
        progression.append({
            "date":          workout.started_at.date().isoformat() if workout.started_at else None,
            "workout_id":    workout.id,
            "max_weight_kg": max(weight_values) if weight_values else None,
            "total_sets":    len(sets),
            "total_reps":    sum(reps_values) if reps_values else None,
        })

    return {"done": True, "progression": progression}


def action_get_body_measurement_trend(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: tendencia de mediciones corporales.
    Config: {"limit": int (default 5)}
    """
    limit = config.get("limit", 5)
    if not isinstance(limit, int) or limit < 1:
        limit = 5
    if limit > 50:
        limit = 50

    measurements = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user_id)
        .order_by(BodyMeasurement.created_at.desc())
        .limit(limit)
        .all()
    )

    if not measurements:
        return {"done": False, "reason": "no body measurements found for user"}

    measurements = list(reversed(measurements))  # orden ascendente para trend

    # Delta: última - primera (solo si ambas tienen weight_kg)
    weights_with_value = [m for m in measurements if m.weight_kg is not None]
    if len(weights_with_value) >= 2:
        weight_delta = round(
            weights_with_value[-1].weight_kg - weights_with_value[0].weight_kg, 2
        )
    else:
        weight_delta = None

    return {
        "done":            True,
        "measurements":    [_measurement_to_dict(m) for m in measurements],
        "weight_delta_kg": weight_delta,
    }
