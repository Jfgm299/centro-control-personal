import pytest


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
def body_measurement_id(auth_client, sample_body_measurement_data):
    response = auth_client.post("/api/v1/body-measures/", json=sample_body_measurement_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]