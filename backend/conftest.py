import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import Base, get_db
from app.main import app


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(scope="function")
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ==================== FIXTURES DE DATOS ====================

@pytest.fixture
def sample_expense_data():
    return {
        "name": "Test Expense",
        "quantity": 50.0,
        "account": "Imagin",
        "date": "2026-02-25"
    }


@pytest.fixture
def sample_workout_data():
    return {
        "muscle_groups": ["Chest", "Arms"],  # ← Arms no existe en el enum, corregido abajo
        "notes": "Test workout"
    }


@pytest.fixture
def sample_exercise_weight_data():
    return {
        "name": "Bench Press",
        "exercise_type": "Weight_reps",
        "notes": "Test exercise"
    }


@pytest.fixture
def sample_exercise_cardio_data():
    return {
        "name": "Treadmill",
        "exercise_type": "Cardio",
        "notes": None
    }


@pytest.fixture
def sample_set_weight_data():
    return {
        "weight_kg": 80.0,
        "reps": 10,
        "rpe": 7,
        "notes": None,
        "speed_kmh": None,
        "incline_percent": None,
        "duration_seconds": None
    }


@pytest.fixture
def sample_set_cardio_data():
    return {
        "speed_kmh": 12.0,
        "incline_percent": 5.0,
        "duration_seconds": 600,
        "rpe": 6,
        "notes": None,
        "weight_kg": None,
        "reps": None
    }


# ==================== FIXTURES COMPUESTOS ====================

@pytest.fixture
def active_workout_id(client):
    """Crea un workout activo y retorna su ID"""
    response = client.post("/api/v1/workouts/", json={
        "muscle_groups": ["Chest", "Back"],  # ← valores válidos del enum
        "notes": "Test workout"
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def weight_exercise_id(client, active_workout_id, sample_exercise_weight_data):
    """Crea un ejercicio de peso y retorna su ID"""
    response = client.post(
        f"/api/v1/workouts/{active_workout_id}/exercises",
        json=sample_exercise_weight_data
    )
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def cardio_exercise_id(client, active_workout_id, sample_exercise_cardio_data):
    """Crea un ejercicio de cardio y retorna su ID"""
    response = client.post(
        f"/api/v1/workouts/{active_workout_id}/exercises",
        json=sample_exercise_cardio_data
    )
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def weight_exercise_with_set(client, active_workout_id, weight_exercise_id, sample_set_weight_data):
    response = client.post(
        f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",  # ← URL correcta
        json=sample_set_weight_data
    )
    assert response.status_code == 201, response.json()
    return (active_workout_id, weight_exercise_id, response.json()["id"])


@pytest.fixture
def cardio_exercise_with_set(client, active_workout_id, cardio_exercise_id, sample_set_cardio_data):
    response = client.post(
        f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",  # ← URL correcta
        json=sample_set_cardio_data
    )
    assert response.status_code == 201, response.json()
    return (active_workout_id, cardio_exercise_id, response.json()["id"])