import pytest
from unittest.mock import patch, AsyncMock
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core import Base, get_db
from app.main import app

from app.modules.flights_tracker.exceptions import (
    FlightNotFoundInAPIError,
    AeroDataBoxTimeoutError,
    AeroDataBoxRateLimitError,
)

from app.modules.macro_tracker.exceptions import (
    ProductNotFoundInAPIError,
    OFFTimeoutError,
    OFFRateLimitError,
)

SQLALCHEMY_TEST_DATABASE_URL = "postgresql://test:test@db_test:5432/test_db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TRUNCATE_SQL = text("""
    TRUNCATE TABLE
        gym_tracker.sets,
        gym_tracker.exercises,
        gym_tracker.workout_muscle_groups,
        gym_tracker.workouts,
        gym_tracker.body_measurements,
        expenses_tracker.expenses,
        flights_tracker.flights,
        core.refresh_tokens,
        core.users
    RESTART IDENTITY CASCADE
""")

TRUNCATE_SQL = text("""
    TRUNCATE TABLE
        gym_tracker.sets,
        gym_tracker.exercises,
        gym_tracker.workout_muscle_groups,
        gym_tracker.workouts,
        gym_tracker.body_measurements,
        expenses_tracker.expenses,
        flights_tracker.flights,
        macro_tracker.diary_entries,
        macro_tracker.user_goals,
        macro_tracker.products,
        core.refresh_tokens,
        core.users
    RESTART IDENTITY CASCADE
""")


@pytest.fixture(scope="session", autouse=True)
def fast_password_hashing():
    """Reduce bcrypt rounds de 12 a 4 — ~256x más rápido en tests"""
    import bcrypt
    with patch("bcrypt.gensalt", return_value=bcrypt.gensalt(rounds=4)):
        yield


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS expenses_tracker CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS gym_tracker CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS flights_tracker CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS macro_tracker CASCADE"))   # ← nuevo
        conn.execute(text("CREATE SCHEMA core"))
        conn.execute(text("CREATE SCHEMA expenses_tracker"))
        conn.execute(text("CREATE SCHEMA gym_tracker"))
        conn.execute(text("CREATE SCHEMA flights_tracker"))
        conn.execute(text("CREATE SCHEMA macro_tracker"))                   # ← nuevo
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS expenses_tracker CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS gym_tracker CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS flights_tracker CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS macro_tracker CASCADE"))   # ← nuevo


@pytest.fixture(scope="function")
def db(setup_database):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        with engine.begin() as conn:
            conn.execute(TRUNCATE_SQL)


def make_db_override(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    return override_get_db


@pytest.fixture(scope="function")
def client(db):
    """Client SIN token — para tests de auth"""
    app.dependency_overrides[get_db] = make_db_override(db)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client(db):
    """Client autenticado con usuario principal"""
    app.dependency_overrides[get_db] = make_db_override(db)
    with TestClient(app) as c:
        c.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "testpassword"
        })
        response = c.post("/api/v1/auth/login", json={
            "email": "test@test.com",
            "password": "testpassword"
        })
        token = response.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client_with_refresh(db):
    """Client autenticado que también expone el refresh_token"""
    app.dependency_overrides[get_db] = make_db_override(db)
    with TestClient(app) as c:
        c.post("/api/v1/auth/register", json={
            "email": "test@test.com",
            "username": "testuser",
            "password": "testpassword"
        })
        response = c.post("/api/v1/auth/login", json={
            "email": "test@test.com",
            "password": "testpassword"
        })
        data = response.json()
        c.headers.update({"Authorization": f"Bearer {data['access_token']}"})
        c.refresh_token = data["refresh_token"]
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def other_auth_client(db):
    """Client autenticado con segundo usuario — para tests de ownership"""
    app.dependency_overrides[get_db] = make_db_override(db)
    with TestClient(app) as c:
        c.post("/api/v1/auth/register", json={
            "email": "other@test.com",
            "username": "otheruser",
            "password": "testpassword"
        })
        response = c.post("/api/v1/auth/login", json={
            "email": "other@test.com",
            "password": "testpassword"
        })
        token = response.json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
    app.dependency_overrides.clear()


# ==================== SAMPLE DATA ====================

@pytest.fixture
def sample_expense_data():
    return {"name": "Test Expense", "quantity": 50.0, "account": "Imagin"}

@pytest.fixture
def sample_workout_data():
    return {"muscle_groups": ["Chest", "Back"], "notes": "Test workout"}

@pytest.fixture
def sample_exercise_weight_data():
    return {"name": "Bench Press", "exercise_type": "Weight_reps", "notes": "Test exercise"}

@pytest.fixture
def sample_exercise_cardio_data():
    return {"name": "Treadmill", "exercise_type": "Cardio", "notes": None}

@pytest.fixture
def sample_set_weight_data():
    return {"weight_kg": 80.0, "reps": 10, "rpe": 7, "notes": None,
            "speed_kmh": None, "incline_percent": None, "duration_seconds": None}

@pytest.fixture
def sample_set_cardio_data():
    return {"speed_kmh": 12.0, "incline_percent": 5.0, "duration_seconds": 600,
            "rpe": 6, "notes": None, "weight_kg": None, "reps": None}

@pytest.fixture
def sample_body_measurement_data():
    return {"weight_kg": 75.0, "body_fat_percent": 15.0, "notes": "Morning measurement"}


# ==================== FIXTURES COMPUESTOS (gym / expenses) ====================

@pytest.fixture
def active_workout_id(auth_client):
    response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Chest", "Back"], "notes": "Test workout"})
    assert response.status_code == 201, response.json()
    return response.json()["id"]

@pytest.fixture
def ended_workout_id(auth_client, active_workout_id):
    response = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={"notes": "Finished"})
    assert response.status_code == 201, response.json()
    return active_workout_id

@pytest.fixture
def weight_exercise_id(auth_client, active_workout_id, sample_exercise_weight_data):
    response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/exercises", json=sample_exercise_weight_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]

@pytest.fixture
def cardio_exercise_id(auth_client, active_workout_id, sample_exercise_cardio_data):
    response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/exercises", json=sample_exercise_cardio_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]

@pytest.fixture
def weight_exercise_with_set(auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
    response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets", json=sample_set_weight_data)
    assert response.status_code == 201, response.json()
    return (active_workout_id, weight_exercise_id, response.json()["id"])

@pytest.fixture
def cardio_exercise_with_set(auth_client, active_workout_id, cardio_exercise_id, sample_set_cardio_data):
    response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets", json=sample_set_cardio_data)
    assert response.status_code == 201, response.json()
    return (active_workout_id, cardio_exercise_id, response.json()["id"])

@pytest.fixture
def expense_id(auth_client, sample_expense_data):
    response = auth_client.post("/api/v1/expenses/", json=sample_expense_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]

@pytest.fixture
def body_measurement_id(auth_client, sample_body_measurement_data):
    response = auth_client.post("/api/v1/body-measures/", json=sample_body_measurement_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


# ==================== FLIGHTS TRACKER — MOCK DATA ====================

MOCK_FLIGHT_RAW = {
    "number": "VY1234",
    "status": "Arrived",
    "greatCircleDistance": {
        "km": 621.5, "mile": 386.2, "nm": 335.6, "meter": 621500, "feet": 2038700
    },
    "departure": {
        "airport": {
            "iata": "MAD", "icao": "LEMD", "name": "Madrid Barajas",
            "municipalityName": "Madrid", "countryCode": "ES",
            "timeZone": "Europe/Madrid",
            "location": {"lat": 40.4719, "lon": -3.5626}
        },
        "scheduledTime": {"local": "2025-06-15 10:00+02:00", "utc": "2025-06-15 08:00Z"},
        "runwayTime": {"local": "2025-06-15 10:18+02:00"},
        "terminal": "T4", "gate": "B22",
        "quality": ["Basic", "Live"]
    },
    "arrival": {
        "airport": {
            "iata": "BCN", "icao": "LEBL", "name": "Barcelona El Prat",
            "municipalityName": "Barcelona", "countryCode": "ES",
            "timeZone": "Europe/Madrid",
            "location": {"lat": 41.2971, "lon": 2.0785}
        },
        "scheduledTime": {"local": "2025-06-15 11:15+02:00"},
        "runwayTime": {"local": "2025-06-15 11:22+02:00"},
        "terminal": "T1", "baggageBelt": "5",
        "quality": ["Basic", "Live"]
    },
    "airline": {"iata": "VY", "icao": "VLG", "name": "Vueling"},
    "aircraft": {"model": "Airbus A320", "reg": "EC-MGY", "modeS": "3443C2"},
    "lastUpdatedUtc": "2025-06-15T09:30:00Z",
    "codeshareStatus": "IsOperator",
    "isCargo": False
}

# Mock para vuelos futuros: sin runwayTime ni scheduledTime pasadas,
# para que _is_past() devuelva False correctamente.
def _make_future_mock_raw():
    future_local = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d") + " 10:00+02:00"
    future_arr   = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d") + " 11:15+02:00"
    return {
        "number": "VY1234",
        "status": "Expected",
        "greatCircleDistance": {
            "km": 621.5, "mile": 386.2, "nm": 335.6, "meter": 621500, "feet": 2038700
        },
        "departure": {
            "airport": {
                "iata": "MAD", "icao": "LEMD", "name": "Madrid Barajas",
                "municipalityName": "Madrid", "countryCode": "ES",
                "timeZone": "Europe/Madrid",
                "location": {"lat": 40.4719, "lon": -3.5626}
            },
            "scheduledTime": {"local": future_local},
            "terminal": "T4", "gate": "B22",
            "quality": ["Basic"]
        },
        "arrival": {
            "airport": {
                "iata": "BCN", "icao": "LEBL", "name": "Barcelona El Prat",
                "municipalityName": "Barcelona", "countryCode": "ES",
                "timeZone": "Europe/Madrid",
                "location": {"lat": 41.2971, "lon": 2.0785}
            },
            "scheduledTime": {"local": future_arr},
            "terminal": "T1",
            "quality": ["Basic"]
        },
        "airline": {"iata": "VY", "icao": "VLG", "name": "Vueling"},
        "aircraft": {"model": "Airbus A320", "reg": "EC-MGY", "modeS": "3443C2"},
        "lastUpdatedUtc": "2026-02-28T09:30:00Z",
        "codeshareStatus": "IsOperator",
        "isCargo": False
    }


# ==================== FLIGHTS TRACKER — MOCK FIXTURES ====================

@pytest.fixture
def mock_aerodatabox():
    """Parchea AeroDataBoxClient.get_flight para devolver MOCK_FLIGHT_RAW"""
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock,
        return_value=MOCK_FLIGHT_RAW
    ):
        yield


@pytest.fixture
def mock_aerodatabox_not_found():
    """Parchea get_flight para lanzar FlightNotFoundInAPIError"""
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock,
        side_effect=FlightNotFoundInAPIError("XX9999", "2025-06-15")
    ):
        yield


@pytest.fixture
def mock_aerodatabox_timeout():
    """Parchea get_flight para lanzar AeroDataBoxTimeoutError"""
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock,
        side_effect=AeroDataBoxTimeoutError()
    ):
        yield


@pytest.fixture
def mock_aerodatabox_rate_limit():
    """Parchea get_flight para lanzar AeroDataBoxRateLimitError"""
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock,
        side_effect=AeroDataBoxRateLimitError()
    ):
        yield


@pytest.fixture
def mock_aerodatabox_future():
    """Parchea get_flight para devolver un vuelo futuro (sin tiempos reales pasados)"""
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock,
        return_value=_make_future_mock_raw()
    ):
        yield


# ==================== FLIGHTS TRACKER — SAMPLE DATA ====================

@pytest.fixture
def past_flight_data():
    return {
        "flight_number": "VY1234",
        "flight_date": "2025-06-15",
    }


@pytest.fixture
def future_flight_data():
    future_date = (date.today() + timedelta(days=30)).isoformat()
    return {
        "flight_number": "VY1234",
        "flight_date": future_date,
    }


# ==================== FLIGHTS TRACKER — FIXTURES COMPUESTOS ====================

@pytest.fixture
def created_flight_id(auth_client, mock_aerodatabox, past_flight_data):
    """Crea un vuelo pasado en BD y retorna su id"""
    response = auth_client.post("/api/v1/flights/", json=past_flight_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def future_flight_id(auth_client, mock_aerodatabox_future, future_flight_data):
    """Crea un vuelo futuro en BD y retorna su id"""
    response = auth_client.post("/api/v1/flights/", json=future_flight_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def multiple_flights(auth_client, mock_aerodatabox):
    """Crea 5 vuelos pasados en BD para tests del pasaporte"""
    # Fechas dentro del rango ±1 año desde hoy (28 Feb 2026)
    past_dates = [
        (date.today() - timedelta(days=30)).isoformat(),
        (date.today() - timedelta(days=60)).isoformat(),
        (date.today() - timedelta(days=90)).isoformat(),
        (date.today() - timedelta(days=120)).isoformat(),
        (date.today() - timedelta(days=150)).isoformat(),
    ]
    flight_numbers = ["VY1234", "IB3456", "VY5678", "FR9012", "IB7890"]
    ids = []
    for fn, fd in zip(flight_numbers, past_dates):
        response = auth_client.post("/api/v1/flights/", json={"flight_number": fn, "flight_date": fd})
        assert response.status_code == 201, response.json()
        ids.append(response.json()["id"])
    return ids


# ==================== MACRO TRACKER — MOCK DATA ====================

MOCK_PRODUCT_RAW = {
    "code": "8480000342591",
    "status": 1,
    "product": {
        "code": "8480000342591",
        "product_name": "Arroz redondo",
        "brands": "Hacendado",
        "serving_size": "100g",
        "serving_quantity": 100.0,
        "nutrition_grades": "b",
        "image_front_small_url": "https://images.openfoodfacts.org/arroz.jpg",
        "categories_tags": ["en:cereals", "en:rices"],
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
    },
}

MOCK_PRODUCT_PARTIAL_RAW = {
    "code": "1234567890123",
    "status": 1,
    "product": {
        "code": "1234567890123",
        "product_name": "Producto incompleto",
        "brands": "MarcaX",
        "nutriments": {
            "energy-kcal_100g": 200.0,
            # Sin proteínas, grasas, etc. — caso real frecuente en OFF
        },
    },
}


# ==================== MACRO TRACKER — MOCK FIXTURES ====================

@pytest.fixture
def mock_off_client():
    """Parchea OpenFoodFactsClient.get_product → producto completo"""
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock,
        return_value=MOCK_PRODUCT_RAW["product"],
    ):
        yield


@pytest.fixture
def mock_off_not_found():
    """Parchea get_product → ProductNotFoundInAPIError"""
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock,
        side_effect=ProductNotFoundInAPIError("0000000000000"),
    ):
        yield


@pytest.fixture
def mock_off_timeout():
    """Parchea get_product → OFFTimeoutError"""
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock,
        side_effect=OFFTimeoutError(),
    ):
        yield


@pytest.fixture
def mock_off_rate_limit():
    """Parchea get_product → OFFRateLimitError"""
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock,
        side_effect=OFFRateLimitError(),
    ):
        yield


@pytest.fixture
def mock_off_partial():
    """Parchea get_product → producto con solo calorías (campos parciales)"""
    with patch(
        "app.modules.macro_tracker.openfoodfacts_client.OpenFoodFactsClient.get_product",
        new_callable=AsyncMock,
        return_value=MOCK_PRODUCT_PARTIAL_RAW["product"],
    ):
        yield


# ==================== MACRO TRACKER — SAMPLE DATA ====================

@pytest.fixture
def sample_barcode():
    return "8480000342591"


@pytest.fixture
def sample_diary_entry_data():
    """DiaryEntryCreate válido — requiere cached_product_id para el product_id"""
    return {
        "entry_date": date.today().isoformat(),
        "meal_type": "lunch",
        "amount_g": 150.0,
    }


# ==================== MACRO TRACKER — FIXTURES COMPUESTOS ====================

@pytest.fixture
def cached_product_id(auth_client, mock_off_client, sample_barcode):
    """Escanea el barcode mock → guarda el producto en BD → devuelve su id"""
    response = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
    assert response.status_code == 200, response.json()
    return response.json()["id"]


@pytest.fixture
def partial_product_id(auth_client, mock_off_partial):
    """Producto con solo calorías en BD"""
    response = auth_client.get("/api/v1/macros/products/barcode/1234567890123")
    assert response.status_code == 200, response.json()
    return response.json()["id"]


@pytest.fixture
def diary_entry_id(auth_client, cached_product_id, sample_diary_entry_data):
    """Crea una entrada de diario y devuelve su id"""
    data = {**sample_diary_entry_data, "product_id": cached_product_id}
    response = auth_client.post("/api/v1/macros/diary", json=data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def multiple_diary_entries(auth_client, mock_off_client, sample_barcode):
    """Crea 10 entradas en 5 días distintos para tests de stats"""
    product_resp = auth_client.get(f"/api/v1/macros/products/barcode/{sample_barcode}")
    product_id = product_resp.json()["id"]

    ids = []
    meal_types = ["breakfast", "lunch", "dinner", "morning_snack", "afternoon_snack",
                  "breakfast", "lunch", "dinner", "breakfast", "lunch"]
    for i, meal in enumerate(meal_types):
        entry_date = (date.today() - timedelta(days=i % 5)).isoformat()
        resp = auth_client.post("/api/v1/macros/diary", json={
            "product_id": product_id,
            "entry_date": entry_date,
            "meal_type": meal,
            "amount_g": 100.0 + i * 10,
        })
        assert resp.status_code == 201, resp.json()
        ids.append(resp.json()["id"])
    return ids


@pytest.fixture
def user_goal_id(auth_client):
    """Crea/devuelve los objetivos del usuario de test"""
    response = auth_client.get("/api/v1/macros/goals")
    assert response.status_code == 200, response.json()
    return response.json()["id"]