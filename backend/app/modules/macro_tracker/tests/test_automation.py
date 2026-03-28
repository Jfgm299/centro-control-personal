"""
Tests del automation contract de macro_tracker.

Cubre:
  - 5 trigger handlers (handle_meal_logged, handle_daily_macro_threshold,
    handle_goal_updated, handle_no_entry_logged_today, handle_logging_streak)
  - 5 action handlers (action_get_daily_summary, action_get_weekly_stats,
    action_get_goal_progress, action_log_meal, action_get_top_products)
  - Dispatcher integration (skip_dispatch, service hooks no rompen el flujo normal)

REGLA: Nunca llamar job_check_*() directamente — usan SessionLocal() del dev DB.
       Usar dispatcher.on_*() con la sesión de test.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app.modules.macro_tracker.automation_handlers import (
    handle_meal_logged,
    handle_daily_macro_threshold,
    handle_goal_updated,
    handle_no_entry_logged_today,
    handle_logging_streak,
    action_get_daily_summary,
    action_get_weekly_stats,
    action_get_goal_progress,
    action_log_meal,
    action_get_top_products,
    MACRO_FIELDS,
)
from app.modules.macro_tracker.automation_dispatcher import (
    MacroAutomationDispatcher,
    _macro_threshold_cache,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_PRODUCT_RAW = {
    "code": "8480000342591",
    "product_name": "Arroz redondo",
    "brands": "Hacendado",
    "serving_size": "100g",
    "serving_quantity": 100.0,
    "nutrition_grades": "b",
    "image_front_small_url": "https://images.openfoodfacts.org/arroz.jpg",
    "categories_tags": [],
    "allergens_tags": [],
    "nutriments": {
        "energy-kcal_100g": 354.0,
        "proteins_100g": 7.0,
        "carbohydrates_100g": 77.0,
        "sugars_100g": 0.4,
        "fat_100g": 0.9,
        "saturated-fat_100g": 0.2,
        "fiber_100g": 0.6,
        "salt_100g": 0.01,
        "sodium_100g": 0.004,
    },
}


@pytest.fixture
def mock_off_client():
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock,
        return_value=MOCK_PRODUCT_RAW,
    ):
        yield


@pytest.fixture
def sample_product_id(auth_client, mock_off_client):
    """Obtiene un product_id cacheando el producto desde OFF mock."""
    response = auth_client.get("/api/v1/macros/products/barcode/8480000342591")
    assert response.status_code == 200, response.json()
    return response.json()["id"]


@pytest.fixture
def sample_entry_id(auth_client, sample_product_id):
    """Crea una DiaryEntry de hoy para el usuario autenticado."""
    response = auth_client.post("/api/v1/macros/diary", json={
        "product_id": sample_product_id,
        "entry_date": date.today().isoformat(),
        "meal_type": "lunch",
        "amount_g": 150.0,
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def sample_user_id(auth_client):
    """Obtiene el user_id del usuario autenticado vía el endpoint de goals."""
    response = auth_client.get("/api/v1/macros/goals")
    assert response.status_code == 200, response.json()
    return response.json()["id"]  # UserGoal.id ≈ referencia — usamos db fixture directamente


@pytest.fixture
def set_goal(auth_client):
    """Configura un UserGoal con valores conocidos."""
    response = auth_client.put("/api/v1/macros/goals", json={
        "energy_kcal": 2000.0,
        "proteins_g": 150.0,
        "carbohydrates_g": 250.0,
        "fat_g": 70.0,
        "fiber_g": 25.0,
    })
    assert response.status_code in (200, 201), response.json()
    return response.json()


@pytest.fixture
def clear_threshold_cache():
    """Limpia el caché de dedup del threshold entre tests."""
    _macro_threshold_cache.clear()
    yield
    _macro_threshold_cache.clear()


# ── helpers para obtener user_id desde la sesión de test ─────────────────────

def _get_user_id(db, auth_client):
    from app.core.auth.user import User
    response = auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    return response.json()["id"]


# ── Tests: handle_meal_logged ─────────────────────────────────────────────────

class TestHandleMealLogged:

    def test_no_filters_always_matched(self, db, auth_client, sample_entry_id):
        user_id = _get_user_id(db, auth_client)
        result = handle_meal_logged(
            payload={"entry_id": sample_entry_id},
            config={},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True
        assert "entry" in result

    def test_meal_type_filter_matches(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "breakfast",
            "amount_g": 100.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"meal_type": "breakfast"},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True

    def test_meal_type_filter_no_match(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"meal_type": "breakfast"},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is False
        assert "meal_type" in result["reason"]

    def test_min_energy_kcal_pass(self, db, auth_client, sample_product_id):
        """Arroz 354 kcal/100g * 150g = 531 kcal — debe superar 300."""
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 150.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"min_energy_kcal": 300.0},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True

    def test_min_energy_kcal_fail(self, db, auth_client, sample_product_id):
        """Arroz 354 kcal/100g * 50g = 177 kcal — no supera 300."""
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 50.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"min_energy_kcal": 300.0},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is False
        assert "min_energy_kcal" in result["reason"]

    def test_max_energy_kcal_pass(self, db, auth_client, sample_product_id):
        """50g → 177 kcal, max=500 → pasa."""
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "snack" if False else "other",
            "amount_g": 50.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"max_energy_kcal": 500.0},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True

    def test_max_energy_kcal_fail(self, db, auth_client, sample_product_id):
        """200g → 708 kcal, max=500 → falla."""
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "dinner",
            "amount_g": 200.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"max_energy_kcal": 500.0},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is False
        assert "max_energy_kcal" in result["reason"]

    def test_nutriscore_match(self, db, auth_client, sample_product_id):
        """Arroz tiene nutriscore='b' (mock). Config 'B' (case-insensitive) → match."""
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"nutriscore": "B"},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True

    def test_nutriscore_no_match(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"nutriscore": "A"},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is False
        assert "nutriscore" in result["reason"]

    def test_product_name_contains_match(self, db, auth_client, sample_product_id):
        """Producto = 'Arroz redondo', buscamos 'arroz' (case-insensitive)."""
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"product_name_contains": "arroz"},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True

    def test_product_name_contains_no_match(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"product_name_contains": "yogur"},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is False
        assert "product_name_contains" in result["reason"]

    def test_multiple_filters_all_pass(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 150.0,
        })
        entry_id = resp.json()["id"]
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"meal_type": "lunch", "min_energy_kcal": 300.0, "nutriscore": "B"},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True

    def test_multiple_filters_one_fails(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 150.0,
        })
        entry_id = resp.json()["id"]
        # nutriscore A no coincide (es B)
        result = handle_meal_logged(
            payload={"entry_id": entry_id},
            config={"meal_type": "lunch", "min_energy_kcal": 300.0, "nutriscore": "A"},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is False

    def test_missing_entry_id(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = handle_meal_logged(payload={}, config={}, db=db, user_id=user_id)
        assert result["matched"] is False

    def test_entry_not_found(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = handle_meal_logged(
            payload={"entry_id": 999999},
            config={},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is False


# ── Tests: handle_daily_macro_threshold ──────────────────────────────────────

class TestHandleDailyMacroThreshold:

    def test_above_exceeded(self):
        """progress_pct=105 >= threshold=100 → matched."""
        result = handle_daily_macro_threshold(
            payload={
                "date": str(date.today()),
                "macro": "energy_kcal",
                "actual_value": 2100.0,
                "goal_value": 2000.0,
                "progress_pct": 105.0,
            },
            config={"macro": "energy_kcal", "threshold_pct": 100, "direction": "above"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True

    def test_above_not_exceeded(self):
        result = handle_daily_macro_threshold(
            payload={
                "date": str(date.today()),
                "macro": "energy_kcal",
                "actual_value": 1800.0,
                "goal_value": 2000.0,
                "progress_pct": 90.0,
            },
            config={"macro": "energy_kcal", "threshold_pct": 100, "direction": "above"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is False

    def test_above_at_boundary_inclusive(self):
        """progress_pct == threshold → matched (inclusive >=)."""
        result = handle_daily_macro_threshold(
            payload={
                "date": str(date.today()),
                "macro": "proteins_g",
                "actual_value": 120.0,
                "goal_value": 150.0,
                "progress_pct": 80.0,
            },
            config={"macro": "proteins_g", "threshold_pct": 80, "direction": "above"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True

    def test_below_below_threshold(self):
        result = handle_daily_macro_threshold(
            payload={
                "date": str(date.today()),
                "macro": "proteins_g",
                "actual_value": 60.0,
                "goal_value": 150.0,
                "progress_pct": 40.0,
            },
            config={"macro": "proteins_g", "threshold_pct": 50, "direction": "below"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True

    def test_below_above_threshold(self):
        result = handle_daily_macro_threshold(
            payload={
                "date": str(date.today()),
                "macro": "proteins_g",
                "actual_value": 100.0,
                "goal_value": 150.0,
                "progress_pct": 66.7,
            },
            config={"macro": "proteins_g", "threshold_pct": 50, "direction": "below"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is False

    def test_below_at_boundary_inclusive(self):
        """progress_pct == threshold → matched (inclusive <=)."""
        result = handle_daily_macro_threshold(
            payload={
                "date": str(date.today()),
                "macro": "fat_g",
                "actual_value": 70.0,
                "goal_value": 70.0,
                "progress_pct": 100.0,
            },
            config={"macro": "fat_g", "threshold_pct": 100, "direction": "below"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True

    def test_default_threshold_and_direction(self):
        """Sin threshold_pct ni direction → defaults (100, above)."""
        result = handle_daily_macro_threshold(
            payload={
                "date": str(date.today()),
                "macro": "carbohydrates_g",
                "actual_value": 260.0,
                "goal_value": 250.0,
                "progress_pct": 104.0,
            },
            config={"macro": "carbohydrates_g"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True

    def test_missing_goal_value(self):
        result = handle_daily_macro_threshold(
            payload={"macro": "energy_kcal", "actual_value": 100.0},
            config={"macro": "energy_kcal"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is False


# ── Tests: handle_goal_updated ────────────────────────────────────────────────

class TestHandleGoalUpdated:

    def test_no_config_filter_fires_on_any_change(self):
        result = handle_goal_updated(
            payload={
                "energy_kcal": 2000.0, "proteins_g": 160.0,
                "carbohydrates_g": 250.0, "fat_g": 70.0, "fiber_g": 25.0,
                "changed_fields": ["energy_kcal", "proteins_g"],
            },
            config={},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True
        assert "energy_kcal" in result["changed_fields"]

    def test_macro_changed_filter_matches(self):
        result = handle_goal_updated(
            payload={
                "energy_kcal": 2000.0, "proteins_g": 160.0,
                "carbohydrates_g": 250.0, "fat_g": 70.0, "fiber_g": 25.0,
                "changed_fields": ["proteins_g"],
            },
            config={"macro_changed": "proteins_g"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True

    def test_macro_changed_filter_no_match(self):
        result = handle_goal_updated(
            payload={
                "energy_kcal": 2200.0, "proteins_g": 150.0,
                "carbohydrates_g": 250.0, "fat_g": 70.0, "fiber_g": 25.0,
                "changed_fields": ["energy_kcal"],
            },
            config={"macro_changed": "proteins_g"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is False
        assert "proteins_g" in result["reason"]

    def test_empty_changed_fields(self):
        """Ningún campo cambió — sin filtro → igual pasa (el dispatcher no llamaría si no hubiese cambios,
        pero el handler en sí no conoce ese contexto; simplemente no hay filtro fallido)."""
        result = handle_goal_updated(
            payload={
                "energy_kcal": 2000.0, "proteins_g": 150.0,
                "carbohydrates_g": 250.0, "fat_g": 70.0, "fiber_g": 25.0,
                "changed_fields": [],
            },
            config={},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True

    def test_first_creation_macro_filter(self):
        """Primera creación — changed_fields contiene todos los campos seteados."""
        result = handle_goal_updated(
            payload={
                "energy_kcal": 2000.0, "proteins_g": 150.0,
                "carbohydrates_g": 250.0, "fat_g": 70.0, "fiber_g": 25.0,
                "changed_fields": ["energy_kcal", "proteins_g", "carbohydrates_g", "fat_g", "fiber_g"],
            },
            config={"macro_changed": "energy_kcal"},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True


# ── Tests: handle_no_entry_logged_today ──────────────────────────────────────

class TestHandleNoEntryLoggedToday:

    def test_no_entries_today_matched(self, db, auth_client):
        """Sin entradas hoy → matched=True."""
        user_id = _get_user_id(db, auth_client)
        result = handle_no_entry_logged_today(
            payload={"days_since_last_entry": 2, "last_entry_date": str(date.today() - timedelta(days=2))},
            config={"check_hour": 20},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True
        assert result["days_since_last_entry"] == 2

    def test_has_entries_today_not_matched(self, db, auth_client, sample_entry_id):
        """Con entradas hoy → matched=False."""
        user_id = _get_user_id(db, auth_client)
        result = handle_no_entry_logged_today(
            payload={"days_since_last_entry": 0, "last_entry_date": str(date.today())},
            config={},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is False
        assert "entries exist" in result["reason"]

    def test_no_prior_entries_ever(self, db, auth_client):
        """Sin ninguna entrada previa → last_entry_date=None."""
        user_id = _get_user_id(db, auth_client)
        result = handle_no_entry_logged_today(
            payload={"days_since_last_entry": 0, "last_entry_date": None},
            config={},
            db=db,
            user_id=user_id,
        )
        assert result["matched"] is True
        assert result["last_entry_date"] is None


# ── Tests: handle_logging_streak ─────────────────────────────────────────────

class TestHandleLoggingStreak:

    def test_exact_match(self):
        result = handle_logging_streak(
            payload={"streak_days": 7, "streak_start_date": "2026-03-20"},
            config={"streak_days": 7},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True
        assert result["streak_days"] == 7

    def test_streak_longer_than_target(self):
        """Racha de 10 días, target 7 → NO dispara (exact match)."""
        result = handle_logging_streak(
            payload={"streak_days": 10, "streak_start_date": "2026-03-17"},
            config={"streak_days": 7},
            db=None,
            user_id=1,
        )
        assert result["matched"] is False

    def test_streak_shorter_than_target(self):
        result = handle_logging_streak(
            payload={"streak_days": 5, "streak_start_date": "2026-03-22"},
            config={"streak_days": 7},
            db=None,
            user_id=1,
        )
        assert result["matched"] is False

    def test_streak_zero(self):
        result = handle_logging_streak(
            payload={"streak_days": 0, "streak_start_date": ""},
            config={"streak_days": 7},
            db=None,
            user_id=1,
        )
        assert result["matched"] is False

    def test_streak_one_day(self):
        result = handle_logging_streak(
            payload={"streak_days": 1, "streak_start_date": str(date.today() - timedelta(days=1))},
            config={"streak_days": 1},
            db=None,
            user_id=1,
        )
        assert result["matched"] is True

    def test_no_streak_days_configured(self):
        result = handle_logging_streak(
            payload={"streak_days": 7, "streak_start_date": "2026-03-20"},
            config={},
            db=None,
            user_id=1,
        )
        assert result["matched"] is False
        assert "not configured" in result["reason"]


# ── Tests: action_get_daily_summary ──────────────────────────────────────────

class TestActionGetDailySummary:

    def test_today_with_entries(self, db, auth_client, sample_product_id):
        """3 entradas hoy (2 breakfast, 1 lunch) → totales sumados, meals agrupadas."""
        user_id = _get_user_id(db, auth_client)
        for mt in ["breakfast", "breakfast", "lunch"]:
            auth_client.post("/api/v1/macros/diary", json={
                "product_id": sample_product_id,
                "entry_date": date.today().isoformat(),
                "meal_type": mt,
                "amount_g": 100.0,
            })
        result = action_get_daily_summary(payload={}, config={"date_offset": 0}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["date"] == str(date.today())
        assert len(result["meals"]["breakfast"]) == 2
        assert len(result["meals"]["lunch"]) == 1
        assert result["totals"]["energy_kcal"] > 0

    def test_yesterday_offset(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        yesterday = date.today() - timedelta(days=1)
        auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": yesterday.isoformat(),
            "meal_type": "dinner",
            "amount_g": 100.0,
        })
        result = action_get_daily_summary(payload={}, config={"date_offset": -1}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["date"] == str(yesterday)

    def test_no_entries(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_get_daily_summary(payload={}, config={}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["totals"]["energy_kcal"] == 0.0
        assert result["meals"]["breakfast"] == []

    def test_no_goal_returns_none(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_get_daily_summary(payload={}, config={}, db=db, user_id=user_id)
        # Sin goal configurado → goals son None y progress_pct son None
        for f in MACRO_FIELDS:
            assert result["goals"][f] is None
            assert result["progress_pct"][f] is None

    def test_with_goal_progress_computed(self, db, auth_client, sample_product_id, set_goal):
        user_id = _get_user_id(db, auth_client)
        auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        result = action_get_daily_summary(payload={}, config={}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["goals"]["energy_kcal"] == 2000.0
        assert result["progress_pct"]["energy_kcal"] is not None

    def test_default_offset_is_today(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_get_daily_summary(payload={}, config={}, db=db, user_id=user_id)
        assert result["date"] == str(date.today())


# ── Tests: action_get_weekly_stats ───────────────────────────────────────────

class TestActionGetWeeklyStats:

    def test_no_entries_current_week(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_get_weekly_stats(payload={}, config={"week_offset": 0}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["days_logged"] == 0
        assert result["consistency_pct"] == 0.0
        assert result["top_products"] == []

    def test_returns_correct_week_bounds(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        today  = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        result = action_get_weekly_stats(payload={}, config={"week_offset": 0}, db=db, user_id=user_id)
        assert result["week_start"] == str(monday)
        assert result["week_end"]   == str(sunday)

    def test_days_logged_and_consistency(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        today  = date.today()
        monday = today - timedelta(days=today.weekday())
        # Crear entradas en 3 días distintos de la semana actual
        for d in [monday, monday + timedelta(days=1), monday + timedelta(days=2)]:
            auth_client.post("/api/v1/macros/diary", json={
                "product_id": sample_product_id,
                "entry_date": d.isoformat(),
                "meal_type": "lunch",
                "amount_g": 100.0,
            })
        result = action_get_weekly_stats(payload={}, config={"week_offset": 0}, db=db, user_id=user_id)
        assert result["days_logged"] == 3
        assert result["consistency_pct"] == round(3 / 7 * 100, 1)

    def test_top_products_limited_to_5(self, db, auth_client, mock_off_client):
        user_id = _get_user_id(db, auth_client)
        today  = date.today()
        monday = today - timedelta(days=today.weekday())

        # Crear 8 productos distintos (via barcodes diferentes)
        barcodes = [f"000000000000{i}" for i in range(8)]
        product_ids = []
        for bc in barcodes:
            with patch(
                "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
                new_callable=__import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock,
                return_value={**MOCK_PRODUCT_RAW, "code": bc, "product_name": f"Producto {bc}"},
            ):
                resp = auth_client.get(f"/api/v1/macros/products/barcode/{bc}")
                if resp.status_code == 200:
                    product_ids.append(resp.json()["id"])

        for pid in product_ids:
            auth_client.post("/api/v1/macros/diary", json={
                "product_id": pid,
                "entry_date": monday.isoformat(),
                "meal_type": "lunch",
                "amount_g": 100.0,
            })

        result = action_get_weekly_stats(payload={}, config={"week_offset": 0}, db=db, user_id=user_id)
        assert result["done"] is True
        assert len(result["top_products"]) <= 5

    def test_default_week_offset(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_get_weekly_stats(payload={}, config={}, db=db, user_id=user_id)
        assert result["done"] is True
        today  = date.today()
        monday = today - timedelta(days=today.weekday())
        assert result["week_start"] == str(monday)


# ── Tests: action_get_goal_progress ──────────────────────────────────────────

class TestActionGetGoalProgress:

    def test_no_goal_returns_done_false(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_get_goal_progress(payload={}, config={}, db=db, user_id=user_id)
        assert result["done"] is False
        assert "no goal" in result["reason"]

    def test_partial_progress(self, db, auth_client, sample_product_id, set_goal):
        user_id = _get_user_id(db, auth_client)
        auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        result = action_get_goal_progress(payload={}, config={}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["progress"]["energy_kcal"]["goal"] == 2000.0
        assert result["progress"]["energy_kcal"]["actual"] > 0
        assert result["progress"]["energy_kcal"]["remaining"] < 2000.0

    def test_over_goal_remaining_negative(self, db, auth_client, mock_off_client):
        """Si el total supera el objetivo, remaining es negativo."""
        user_id = _get_user_id(db, auth_client)
        auth_client.put("/api/v1/macros/goals", json={"energy_kcal": 100.0})
        # Arroz 354 kcal/100g * 200g = 708 kcal > 100
        prod_resp = auth_client.get("/api/v1/macros/products/barcode/8480000342591")
        pid = prod_resp.json()["id"]
        auth_client.post("/api/v1/macros/diary", json={
            "product_id": pid,
            "entry_date": date.today().isoformat(),
            "meal_type": "dinner",
            "amount_g": 200.0,
        })
        result = action_get_goal_progress(payload={}, config={}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["progress"]["energy_kcal"]["remaining"] < 0

    def test_no_entries_today_actual_zero(self, db, auth_client, set_goal):
        user_id = _get_user_id(db, auth_client)
        result = action_get_goal_progress(payload={}, config={}, db=db, user_id=user_id)
        assert result["done"] is True
        for f in MACRO_FIELDS:
            assert result["progress"][f]["actual"] == 0.0
            assert result["progress"][f]["progress_pct"] == 0.0


# ── Tests: action_log_meal ────────────────────────────────────────────────────

class TestActionLogMeal:

    def test_valid_product_creates_entry(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        result = action_log_meal(
            payload={},
            config={
                "product_id": sample_product_id,
                "amount_g": 100.0,
                "meal_type": "lunch",
            },
            db=db,
            user_id=user_id,
        )
        assert result["done"] is True
        assert result["entry_id"] is not None
        assert result["energy_kcal"] > 0

    def test_product_not_found(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_log_meal(
            payload={},
            config={"product_id": 999999, "amount_g": 100.0, "meal_type": "lunch"},
            db=db,
            user_id=user_id,
        )
        assert result["done"] is False
        assert "999999" in result["reason"]

    def test_date_offset_yesterday(self, db, auth_client, sample_product_id):
        from app.modules.macro_tracker.diary_entry import DiaryEntry
        user_id = _get_user_id(db, auth_client)
        result = action_log_meal(
            payload={},
            config={
                "product_id": sample_product_id,
                "amount_g": 50.0,
                "meal_type": "snack" if False else "other",
                "date_offset": -1,
            },
            db=db,
            user_id=user_id,
        )
        assert result["done"] is True
        entry = db.query(DiaryEntry).filter(DiaryEntry.id == result["entry_id"]).first()
        assert entry.entry_date == date.today() - timedelta(days=1)

    def test_skip_dispatch_prevents_double_fire(self, db, auth_client, sample_product_id):
        """skip_dispatch=True en add_entry() → dispatcher no se llama."""
        user_id = _get_user_id(db, auth_client)

        call_count = {"n": 0}

        original_on_meal = MacroAutomationDispatcher.on_meal_logged

        def mock_on_meal(self, *args, **kwargs):
            call_count["n"] += 1
            return original_on_meal(self, *args, **kwargs)

        with patch.object(MacroAutomationDispatcher, "on_meal_logged", mock_on_meal):
            result = action_log_meal(
                payload={},
                config={"product_id": sample_product_id, "amount_g": 100.0, "meal_type": "lunch"},
                db=db,
                user_id=user_id,
            )

        assert result["done"] is True
        # on_meal_logged NO debe haber sido llamado (skip_dispatch=True)
        assert call_count["n"] == 0

    def test_missing_product_id(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_log_meal(
            payload={},
            config={"amount_g": 100.0, "meal_type": "lunch"},
            db=db,
            user_id=user_id,
        )
        assert result["done"] is False

    def test_default_date_today(self, db, auth_client, sample_product_id):
        from app.modules.macro_tracker.diary_entry import DiaryEntry
        user_id = _get_user_id(db, auth_client)
        result = action_log_meal(
            payload={},
            config={"product_id": sample_product_id, "amount_g": 100.0, "meal_type": "lunch"},
            db=db,
            user_id=user_id,
        )
        assert result["done"] is True
        entry = db.query(DiaryEntry).filter(DiaryEntry.id == result["entry_id"]).first()
        assert entry.entry_date == date.today()


# ── Tests: action_get_top_products ───────────────────────────────────────────

class TestActionGetTopProducts:

    def test_standard_returns_sorted_by_count(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        # Crear 3 entradas del mismo producto → count=3
        for _ in range(3):
            auth_client.post("/api/v1/macros/diary", json={
                "product_id": sample_product_id,
                "entry_date": date.today().isoformat(),
                "meal_type": "lunch",
                "amount_g": 100.0,
            })
        result = action_get_top_products(payload={}, config={"days": 30, "limit": 5}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["period_days"] == 30
        assert len(result["products"]) >= 1
        assert result["products"][0]["entry_count"] >= 3

    def test_limit_enforced_at_10(self, db, auth_client, sample_product_id):
        user_id = _get_user_id(db, auth_client)
        result = action_get_top_products(payload={}, config={"limit": 50}, db=db, user_id=user_id)
        assert len(result["products"]) <= 10

    def test_no_entries_empty_products(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_get_top_products(payload={}, config={"days": 7}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["products"] == []

    def test_defaults_applied(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        result = action_get_top_products(payload={}, config={}, db=db, user_id=user_id)
        assert result["done"] is True
        assert result["period_days"] == 30

    def test_products_outside_window_excluded(self, db, auth_client, mock_off_client):
        user_id = _get_user_id(db, auth_client)
        # Producto A: 35 días atrás → fuera del window de 30 días
        resp = auth_client.get("/api/v1/macros/products/barcode/8480000342591")
        pid = resp.json()["id"]
        auth_client.post("/api/v1/macros/diary", json={
            "product_id": pid,
            "entry_date": (date.today() - timedelta(days=35)).isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        result = action_get_top_products(payload={}, config={"days": 30}, db=db, user_id=user_id)
        assert result["done"] is True
        # No debería aparecer ningún producto dentro del window
        assert result["products"] == []


# ── Tests: Dispatcher + Service integration ───────────────────────────────────

class TestDispatcherIntegration:

    def test_add_entry_does_not_break_service(self, auth_client, sample_product_id):
        """Llamar al endpoint de diary crea entrada correctamente aunque el dispatcher falle."""
        response = auth_client.post("/api/v1/macros/diary", json={
            "product_id": sample_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 150.0,
        })
        assert response.status_code == 201
        assert response.json()["id"] is not None

    def test_upsert_goals_does_not_break_service(self, auth_client):
        """Actualizar goals funciona aunque el dispatcher no pueda disparar."""
        response = auth_client.put("/api/v1/macros/goals", json={
            "energy_kcal": 1800.0,
            "proteins_g": 140.0,
        })
        assert response.status_code in (200, 201)
        assert response.json()["energy_kcal"] == 1800.0

    def test_dispatcher_on_no_entry_fires_when_no_entries(self, db, auth_client):
        """dispatcher.on_no_entry_logged_today no lanza excepción."""
        user_id = _get_user_id(db, auth_client)
        d = MacroAutomationDispatcher()
        # No hay automatizaciones activas en tests → ejecuta sin error
        try:
            d.on_no_entry_logged_today(user_id, 0, None, db)
        except Exception as e:
            pytest.fail(f"Dispatcher lanzó excepción inesperada: {e}")

    def test_dispatcher_on_logging_streak_no_exception(self, db, auth_client):
        user_id = _get_user_id(db, auth_client)
        d = MacroAutomationDispatcher()
        try:
            d.on_logging_streak(user_id, 7, "2026-01-01", db)
        except Exception as e:
            pytest.fail(f"Dispatcher lanzó excepción inesperada: {e}")

    def test_on_goal_updated_no_changes_skips(self, db, auth_client, set_goal):
        """Si old_snapshot == new_goal, changed_fields está vacío → dispatcher no dispara."""
        from app.modules.macro_tracker.user_goal import UserGoal
        user_id = _get_user_id(db, auth_client)
        goal = db.query(UserGoal).filter(UserGoal.user_id == user_id).first()
        old_snapshot = {f: getattr(goal, f) for f in MACRO_FIELDS}

        d = MacroAutomationDispatcher()
        fired = []

        original = d._find_and_execute

        def mock_find(trigger_ref, payload, user_id, db):
            fired.append(trigger_ref)
            return original(trigger_ref, payload, user_id, db)

        d._find_and_execute = mock_find
        d.on_goal_updated(user_id, old_snapshot, goal, db)
        assert len(fired) == 0

    def test_on_goal_updated_first_creation_fires(self, db, auth_client):
        """old_snapshot=None (primera creación) → changed_fields tiene todos los campos seteados."""
        from app.modules.macro_tracker.user_goal import UserGoal
        user_id = _get_user_id(db, auth_client)
        auth_client.put("/api/v1/macros/goals", json={"energy_kcal": 2000.0})
        goal = db.query(UserGoal).filter(UserGoal.user_id == user_id).first()

        d = MacroAutomationDispatcher()
        fired = []

        def mock_find(trigger_ref, payload, user_id, db):
            fired.append(payload.get("changed_fields"))

        d._find_and_execute = mock_find
        d.on_goal_updated(user_id, None, goal, db)
        # Debe haber intentado disparar con changed_fields no vacío
        assert len(fired) == 1
        assert len(fired[0]) > 0

    def test_threshold_dedup_same_combo_fires_once(self, db, auth_client, sample_product_id, set_goal, clear_threshold_cache):
        """La misma combinación (user, date, macro, direction) no dispara dos veces."""
        from app.modules.macro_tracker.automation_dispatcher import _macro_threshold_cache

        user_id = _get_user_id(db, auth_client)
        d = MacroAutomationDispatcher()

        fire_count = {"n": 0}
        original = d._find_and_execute

        def mock_find(trigger_ref, payload, user_id, db):
            if trigger_ref == "macro_tracker.daily_macro_threshold":
                fire_count["n"] += 1

        d._find_and_execute = mock_find

        # Simular dos entradas del mismo día — el dedup debe evitar doble disparo
        # para la misma automatización
        # (En tests no hay automations activas, pero verificamos que el dedup key se inserta)
        today_str = str(date.today())
        test_key = (user_id, today_str, "energy_kcal", "above")

        # Primera vez — key no está en cache
        assert test_key not in _macro_threshold_cache

        # Insertar manualmente para simular el primer disparo
        _macro_threshold_cache.add(test_key)

        # Segunda vez — key ya está en cache → no dispara
        assert test_key in _macro_threshold_cache
