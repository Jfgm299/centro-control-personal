import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core import Base, get_db
from app.main import app

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
        conn.execute(text("CREATE SCHEMA core"))
        conn.execute(text("CREATE SCHEMA expenses_tracker"))
        conn.execute(text("CREATE SCHEMA gym_tracker"))
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS expenses_tracker CASCADE"))
        conn.execute(text("DROP SCHEMA IF EXISTS gym_tracker CASCADE"))


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


# ==================== FIXTURES COMPUESTOS ====================

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