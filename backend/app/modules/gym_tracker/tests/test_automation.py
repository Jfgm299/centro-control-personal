"""
Tests del automation contract de gym_tracker.

Estructura:
    TestHandleWorkoutStarted         — trigger T1
    TestHandleWorkoutEnded           — trigger T2
    TestHandlePersonalRecordWeight   — trigger T3
    TestHandleBodyMeasurementRecorded — trigger T4
    TestHandleWorkoutInactivity      — trigger T5
    TestActionGetLastWorkoutSummary  — acción A1
    TestActionGetWeeklyStats         — acción A2
    TestActionGetExerciseProgression — acción A3
    TestActionGetBodyMeasurementTrend — acción A4
    TestDispatcherIntegration        — servicios no se rompen con dispatcher
    TestDispatcherInactivityCheck    — on_workout_inactivity_check directo
"""
import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from app.modules.gym_tracker.automation_handlers import (
    handle_workout_started,
    handle_workout_ended,
    handle_personal_record_weight,
    handle_body_measurement_recorded,
    handle_workout_inactivity,
    action_get_last_workout_summary,
    action_get_weekly_stats,
    action_get_exercise_progression,
    action_get_body_measurement_trend,
)
from app.modules.gym_tracker.automation_dispatcher import dispatcher


# ── Fixtures adicionales para automation tests ────────────────────────────────

@pytest.fixture
def ended_workout_with_exercise_and_set(auth_client, active_workout_id, sample_exercise_weight_data, sample_set_weight_data):
    """Crea workout con ejercicio y serie, luego lo termina. Devuelve workout_id."""
    ex_resp = auth_client.post(
        f"/api/v1/workouts/{active_workout_id}/exercises",
        json=sample_exercise_weight_data,
    )
    assert ex_resp.status_code == 201, ex_resp.json()
    ex_id = ex_resp.json()["id"]

    set_resp = auth_client.post(
        f"/api/v1/workouts/{active_workout_id}/{ex_id}/sets",
        json=sample_set_weight_data,
    )
    assert set_resp.status_code == 201, set_resp.json()

    end_resp = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={"notes": "done"})
    assert end_resp.status_code == 201, end_resp.json()
    return active_workout_id


@pytest.fixture
def measurement_with_body_fat_id(auth_client):
    """Crea una medición corporal con body_fat_percentage."""
    resp = auth_client.post(
        "/api/v1/body-measures/",
        json={"weight_kg": 75.0, "body_fat_percentage": 18.0, "notes": "test"},
    )
    assert resp.status_code == 201, resp.json()
    return resp.json()["id"]


# ── T1: handle_workout_started ────────────────────────────────────────────────

class TestHandleWorkoutStarted:

    def test_no_config_always_matches(self, db, active_workout_id):
        result = handle_workout_started(
            payload={"workout_id": active_workout_id, "started_at": "2026-03-26T09:00:00+00:00"},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True
        assert result["workout_id"] == active_workout_id

    def test_day_of_week_filter_matches(self, db, active_workout_id):
        # Parchear datetime.now para que sea lunes (weekday=0)
        monday = datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc)  # lunes real
        with patch("app.modules.gym_tracker.automation_handlers.datetime") as mock_dt:
            mock_dt.now.return_value = monday
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            result = handle_workout_started(
                payload={"workout_id": active_workout_id, "started_at": "2026-03-23T10:00:00+00:00"},
                config={"day_of_week": "monday"},
                db=db,
                user_id=1,
            )
        assert result["matched"] is True

    def test_day_of_week_filter_no_match(self, db, active_workout_id):
        tuesday = datetime(2026, 3, 24, 10, 0, 0, tzinfo=timezone.utc)  # martes
        with patch("app.modules.gym_tracker.automation_handlers.datetime") as mock_dt:
            mock_dt.now.return_value = tuesday
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            result = handle_workout_started(
                payload={"workout_id": active_workout_id, "started_at": "2026-03-24T10:00:00+00:00"},
                config={"day_of_week": "monday"},
                db=db,
                user_id=1,
            )
        assert result["matched"] is False
        assert "day_of_week" in result["reason"]

    def test_invalid_day_of_week_treated_as_no_filter(self, db, active_workout_id):
        result = handle_workout_started(
            payload={"workout_id": active_workout_id, "started_at": "2026-03-26T09:00:00+00:00"},
            config={"day_of_week": "funday"},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_missing_workout_id(self, db):
        result = handle_workout_started(
            payload={"started_at": "2026-03-26T09:00:00+00:00"},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "workout_id" in result["reason"]

    def test_missing_started_at(self, db, active_workout_id):
        result = handle_workout_started(
            payload={"workout_id": active_workout_id},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "started_at" in result["reason"]

    def test_workout_not_found(self, db):
        result = handle_workout_started(
            payload={"workout_id": 99999, "started_at": "2026-03-26T09:00:00+00:00"},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "not found" in result["reason"]


# ── T2: handle_workout_ended ──────────────────────────────────────────────────

class TestHandleWorkoutEnded:

    def _payload(self, workout_id, duration=45, exercises=3, sets=9, muscle_groups=None):
        return {
            "workout_id":       workout_id,
            "duration_minutes": duration,
            "total_exercises":  exercises,
            "total_sets":       sets,
            "muscle_groups":    muscle_groups or ["Chest", "Back"],
        }

    def test_no_config_always_matches(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id),
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True
        assert "workout" in result

    def test_min_duration_met(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id, duration=45),
            config={"min_duration_minutes": 30},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_min_duration_not_met(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id, duration=20),
            config={"min_duration_minutes": 30},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "below minimum" in result["reason"]

    def test_max_duration_exceeded(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id, duration=90),
            config={"max_duration_minutes": 60},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "above maximum" in result["reason"]

    def test_min_exercises_not_met(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id, exercises=2),
            config={"min_exercises": 4},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "below minimum" in result["reason"]

    def test_min_sets_not_met(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id, sets=6),
            config={"min_sets": 10},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "below minimum" in result["reason"]

    def test_required_muscle_groups_all_present(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id, muscle_groups=["Chest", "Back", "Legs"]),
            config={"required_muscle_groups": ["Chest", "Back"]},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_required_muscle_groups_missing(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id, muscle_groups=["Chest", "Back"]),
            config={"required_muscle_groups": ["Chest", "Legs"]},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "missing required muscle groups" in result["reason"]

    def test_invalid_config_min_greater_than_max(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id),
            config={"min_duration_minutes": 90, "max_duration_minutes": 30},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "invalid config" in result["reason"]

    def test_missing_workout_id(self, db):
        result = handle_workout_ended(
            payload={"duration_minutes": 45},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False

    def test_workout_not_found(self, db):
        result = handle_workout_ended(
            payload=self._payload(99999),
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "not found" in result["reason"]

    def test_all_filters_pass_simultaneously(self, db, ended_workout_id):
        result = handle_workout_ended(
            payload=self._payload(ended_workout_id, duration=60, exercises=4, sets=12, muscle_groups=["Chest"]),
            config={
                "min_duration_minutes":   30,
                "min_exercises":          3,
                "min_sets":               10,
                "required_muscle_groups": ["Chest"],
            },
            db=db,
            user_id=1,
        )
        assert result["matched"] is True


# ── T3: handle_personal_record_weight ────────────────────────────────────────

class TestHandlePersonalRecordWeight:

    def _payload(self, exercise_name="Bench Press", new_weight=100.0, prev=90.0, reps=8, workout_id=1, set_id=1):
        return {
            "exercise_name":      exercise_name,
            "new_weight_kg":      new_weight,
            "previous_record_kg": prev,
            "reps":               reps,
            "workout_id":         workout_id,
            "set_id":             set_id,
        }

    def test_new_record_no_config(self, db):
        result = handle_personal_record_weight(
            payload=self._payload(),
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True
        assert result["new_weight_kg"] == 100.0
        assert result["previous_record_kg"] == 90.0

    def test_first_set_ever_no_previous(self, db):
        result = handle_personal_record_weight(
            payload=self._payload(prev=None),
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True
        assert result["previous_record_kg"] is None

    def test_exercise_name_filter_match(self, db):
        result = handle_personal_record_weight(
            payload=self._payload(exercise_name="Bench Press"),
            config={"exercise_name": "Bench Press"},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_exercise_name_filter_no_match(self, db):
        result = handle_personal_record_weight(
            payload=self._payload(exercise_name="Squat"),
            config={"exercise_name": "Bench Press"},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "exercise_name filter" in result["reason"]

    def test_exercise_name_case_insensitive(self, db):
        result = handle_personal_record_weight(
            payload=self._payload(exercise_name="Bench Press"),
            config={"exercise_name": "bench press"},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_min_weight_filter_met(self, db):
        result = handle_personal_record_weight(
            payload=self._payload(new_weight=100.0),
            config={"min_weight_kg": 80},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_min_weight_filter_not_met(self, db):
        result = handle_personal_record_weight(
            payload=self._payload(new_weight=100.0),
            config={"min_weight_kg": 120},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "below min_weight_kg" in result["reason"]

    def test_missing_exercise_name(self, db):
        result = handle_personal_record_weight(
            payload={"new_weight_kg": 100.0, "reps": 8, "workout_id": 1, "set_id": 1},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "exercise_name" in result["reason"]

    def test_missing_new_weight(self, db):
        result = handle_personal_record_weight(
            payload={"exercise_name": "Squat", "reps": 8, "workout_id": 1, "set_id": 1},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "new_weight_kg" in result["reason"]

    def test_weight_zero(self, db):
        result = handle_personal_record_weight(
            payload=self._payload(new_weight=0),
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "must be > 0" in result["reason"]


# ── T4: handle_body_measurement_recorded ─────────────────────────────────────

class TestHandleBodyMeasurementRecorded:

    def _payload(self, mid=1, weight=75.0, body_fat=None):
        return {
            "measurement_id":      mid,
            "weight_kg":           weight,
            "body_fat_percentage": body_fat,
            "recorded_at":         "2026-03-26T08:00:00+00:00",
        }

    def test_no_config_always_matches(self, db, body_measurement_id):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=body_measurement_id),
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True
        assert result["measurement_id"] == body_measurement_id

    def test_min_weight_met(self, db, body_measurement_id):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=body_measurement_id, weight=80.0),
            config={"min_weight_kg": 70},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_min_weight_not_met(self, db, body_measurement_id):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=body_measurement_id, weight=65.0),
            config={"min_weight_kg": 70},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "below min_weight_kg" in result["reason"]

    def test_max_weight_exceeded(self, db, body_measurement_id):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=body_measurement_id, weight=80.0),
            config={"max_weight_kg": 75},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "above max_weight_kg" in result["reason"]

    def test_require_body_fat_present(self, db, measurement_with_body_fat_id):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=measurement_with_body_fat_id, body_fat=18.0),
            config={"require_body_fat": True},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_require_body_fat_missing(self, db, body_measurement_id):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=body_measurement_id, body_fat=None),
            config={"require_body_fat": True},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "body_fat_percentage required" in result["reason"]

    def test_weight_null_with_min_filter(self, db, body_measurement_id):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=body_measurement_id, weight=None),
            config={"min_weight_kg": 70},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "not available" in result["reason"]

    def test_invalid_config_min_greater_than_max(self, db, body_measurement_id):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=body_measurement_id),
            config={"min_weight_kg": 90, "max_weight_kg": 70},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "invalid config" in result["reason"]

    def test_missing_measurement_id(self, db):
        result = handle_body_measurement_recorded(
            payload={"weight_kg": 75.0, "body_fat_percentage": None, "recorded_at": "2026-03-26"},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "measurement_id" in result["reason"]

    def test_measurement_not_found(self, db):
        result = handle_body_measurement_recorded(
            payload=self._payload(mid=99999),
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "not found" in result["reason"]


# ── T5: handle_workout_inactivity ─────────────────────────────────────────────

class TestHandleWorkoutInactivity:

    def test_threshold_exceeded(self, db):
        result = handle_workout_inactivity(
            payload={"days_since_last_workout": 10, "last_workout_date": "2026-03-16"},
            config={"days_without_workout": 7},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True
        assert result["days_since_last_workout"] == 10
        assert result["threshold"] == 7

    def test_threshold_exactly_met(self, db):
        # Límite inclusivo: days_since == threshold → matched
        result = handle_workout_inactivity(
            payload={"days_since_last_workout": 7, "last_workout_date": "2026-03-19"},
            config={"days_without_workout": 7},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True

    def test_threshold_not_reached(self, db):
        result = handle_workout_inactivity(
            payload={"days_since_last_workout": 3, "last_workout_date": "2026-03-23"},
            config={"days_without_workout": 7},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert "only 3 days" in result["reason"]

    def test_never_trained(self, db):
        result = handle_workout_inactivity(
            payload={"days_since_last_workout": None, "last_workout_date": None},
            config={"days_without_workout": 3},
            db=db,
            user_id=1,
        )
        assert result["matched"] is True
        assert result["days_since_last_workout"] is None
        assert "no workouts ever" in result["reason"]

    def test_missing_config(self, db):
        result = handle_workout_inactivity(
            payload={"days_since_last_workout": 10, "last_workout_date": "2026-03-16"},
            config={},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False

    def test_invalid_threshold_zero(self, db):
        result = handle_workout_inactivity(
            payload={"days_since_last_workout": 10, "last_workout_date": "2026-03-16"},
            config={"days_without_workout": 0},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False
        assert ">= 1" in result["reason"]

    def test_non_integer_threshold(self, db):
        result = handle_workout_inactivity(
            payload={"days_since_last_workout": 10, "last_workout_date": "2026-03-16"},
            config={"days_without_workout": "seven"},
            db=db,
            user_id=1,
        )
        assert result["matched"] is False


# ── A1: action_get_last_workout_summary ──────────────────────────────────────

class TestActionGetLastWorkoutSummary:

    def test_no_config_returns_latest_ended_workout(self, db, ended_workout_id):
        result = action_get_last_workout_summary(
            payload={},
            config={},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert "workout" in result
        assert result["workout"]["id"] == ended_workout_id

    def test_specific_workout_id_in_config(self, db, ended_workout_id):
        result = action_get_last_workout_summary(
            payload={},
            config={"workout_id": ended_workout_id},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert result["workout"]["id"] == ended_workout_id

    def test_no_completed_workouts(self, db, active_workout_id):
        # El workout activo aun no ha terminado — no hay ended workouts
        result = action_get_last_workout_summary(
            payload={},
            config={},
            db=db,
            user_id=1,
        )
        assert result["done"] is False
        assert "no completed workouts" in result["reason"]

    def test_workout_not_found(self, db):
        result = action_get_last_workout_summary(
            payload={},
            config={"workout_id": 99999},
            db=db,
            user_id=1,
        )
        assert result["done"] is False
        assert "not found" in result["reason"]

    def test_workout_dict_has_expected_keys(self, db, ended_workout_id):
        result = action_get_last_workout_summary(
            payload={},
            config={"workout_id": ended_workout_id},
            db=db,
            user_id=1,
        )
        w = result["workout"]
        for key in ["id", "started_at", "ended_at", "duration_minutes", "total_exercises", "total_sets", "notes", "muscle_groups"]:
            assert key in w, f"Key '{key}' missing from workout dict"


# ── A2: action_get_weekly_stats ───────────────────────────────────────────────

class TestActionGetWeeklyStats:

    def test_no_workouts_returns_zeros(self, db):
        result = action_get_weekly_stats(
            payload={},
            config={"week_offset": 0},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        stats = result["stats"]
        assert stats["total_workouts"] == 0
        assert stats["total_exercises"] == 0
        assert stats["total_sets"] == 0
        assert stats["muscle_groups"] == []
        assert "week_start" in stats
        assert "week_end" in stats

    def test_current_week_with_workout(self, db, ended_workout_with_exercise_and_set):
        result = action_get_weekly_stats(
            payload={},
            config={"week_offset": 0},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert result["stats"]["total_workouts"] >= 1

    def test_previous_week_no_workouts(self, db):
        result = action_get_weekly_stats(
            payload={},
            config={"week_offset": -1},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert result["stats"]["total_workouts"] == 0

    def test_invalid_week_offset_uses_zero(self, db):
        result = action_get_weekly_stats(
            payload={},
            config={"week_offset": "bad"},
            db=db,
            user_id=1,
        )
        # Debe devolver done: True sin error (usa 0)
        assert result["done"] is True

    def test_stats_keys_present(self, db):
        result = action_get_weekly_stats(payload={}, config={}, db=db, user_id=1)
        for key in ["week_start", "week_end", "total_workouts", "total_exercises", "total_sets", "muscle_groups", "workout_ids"]:
            assert key in result["stats"], f"Key '{key}' missing from stats"


# ── A3: action_get_exercise_progression ──────────────────────────────────────

class TestActionGetExerciseProgression:

    def test_missing_exercise_name(self, db):
        result = action_get_exercise_progression(
            payload={},
            config={},
            db=db,
            user_id=1,
        )
        assert result["done"] is False
        assert "exercise_name is required" in result["reason"]

    def test_exercise_not_found(self, db):
        result = action_get_exercise_progression(
            payload={},
            config={"exercise_name": "Handstand Push-up"},
            db=db,
            user_id=1,
        )
        assert result["done"] is False
        assert "no sets found" in result["reason"]

    def test_valid_exercise_returns_progression(self, db, ended_workout_with_exercise_and_set):
        result = action_get_exercise_progression(
            payload={},
            config={"exercise_name": "Bench Press"},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert len(result["progression"]) >= 1
        entry = result["progression"][0]
        assert "date" in entry
        assert "workout_id" in entry
        assert "max_weight_kg" in entry
        assert "total_sets" in entry

    def test_case_insensitive_match(self, db, ended_workout_with_exercise_and_set):
        result = action_get_exercise_progression(
            payload={},
            config={"exercise_name": "bench press"},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert len(result["progression"]) >= 1

    def test_limit_cap(self, db):
        # limit > 100 debe caparse a 100
        result = action_get_exercise_progression(
            payload={},
            config={"exercise_name": "Nonexistent XYZ", "limit": 999},
            db=db,
            user_id=1,
        )
        # No hay datos — simplemente verifica que no explota
        assert result["done"] is False


# ── A4: action_get_body_measurement_trend ────────────────────────────────────

class TestActionGetBodyMeasurementTrend:

    def test_no_measurements(self, db):
        result = action_get_body_measurement_trend(
            payload={},
            config={},
            db=db,
            user_id=1,
        )
        assert result["done"] is False
        assert "no body measurements" in result["reason"]

    def test_returns_measurements_ascending(self, auth_client, db):
        # Crear 3 mediciones en orden
        for w in [70.0, 72.0, 74.0]:
            auth_client.post("/api/v1/body-measures/", json={"weight_kg": w})

        result = action_get_body_measurement_trend(
            payload={},
            config={"limit": 5},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        weights = [m["weight_kg"] for m in result["measurements"]]
        assert weights == sorted(weights), "Measurements should be in ascending order by recorded_at"

    def test_weight_delta_calculated(self, auth_client, db):
        auth_client.post("/api/v1/body-measures/", json={"weight_kg": 70.0})
        auth_client.post("/api/v1/body-measures/", json={"weight_kg": 75.0})

        result = action_get_body_measurement_trend(
            payload={},
            config={"limit": 5},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert result["weight_delta_kg"] == 5.0

    def test_single_measurement_delta_null(self, db, body_measurement_id):
        result = action_get_body_measurement_trend(
            payload={},
            config={"limit": 5},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert result["weight_delta_kg"] is None

    def test_limit_applied(self, auth_client, db):
        for w in [60.0, 65.0, 70.0, 75.0, 80.0]:
            auth_client.post("/api/v1/body-measures/", json={"weight_kg": w})

        result = action_get_body_measurement_trend(
            payload={},
            config={"limit": 3},
            db=db,
            user_id=1,
        )
        assert result["done"] is True
        assert len(result["measurements"]) == 3


# ── Dispatcher integration: servicios no se rompen ───────────────────────────

class TestDispatcherIntegration:

    def test_start_workout_does_not_break_service(self, auth_client):
        response = auth_client.post("/api/v1/workouts/", json={"notes": "Test"})
        assert response.status_code == 201
        assert "id" in response.json()

    def test_end_workout_does_not_break_service(self, auth_client, active_workout_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={"notes": "done"})
        assert response.status_code == 201

    def test_create_set_does_not_break_service(self, auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        response = auth_client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json=sample_set_weight_data,
        )
        assert response.status_code == 201
        assert "id" in response.json()

    def test_body_measurement_does_not_break_service(self, auth_client):
        response = auth_client.post(
            "/api/v1/body-measures/",
            json={"weight_kg": 75.0, "body_fat_percentage": 18.0},
        )
        assert response.status_code == 201
        assert "id" in response.json()

    def test_pr_trigger_fires_on_new_record(self, auth_client, active_workout_id, weight_exercise_id):
        """Crea dos sets con peso creciente — el segundo debe disparar PR (no falla)."""
        set1 = auth_client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json={"weight_kg": 80.0, "reps": 8, "rpe": 7, "notes": None,
                  "speed_kmh": None, "incline_percent": None, "duration_seconds": None},
        )
        assert set1.status_code == 201

        set2 = auth_client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json={"weight_kg": 90.0, "reps": 6, "rpe": 8, "notes": None,
                  "speed_kmh": None, "incline_percent": None, "duration_seconds": None},
        )
        assert set2.status_code == 201  # no debe romper por el dispatcher


# ── Dispatcher inactivity check ───────────────────────────────────────────────

class TestDispatcherInactivityCheck:

    def test_inactivity_check_user_with_workout(self, db, ended_workout_id):
        """Llama on_workout_inactivity_check con usuario que tiene workout — no explota."""
        dispatcher.on_workout_inactivity_check(user_id=1, db=db)

    def test_inactivity_check_user_never_trained(self, db):
        """Llama con usuario sin workouts — no explota."""
        dispatcher.on_workout_inactivity_check(user_id=1, db=db)
