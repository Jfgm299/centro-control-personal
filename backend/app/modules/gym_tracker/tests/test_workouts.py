def test_start_workout(client):
    response = client.post("/api/workouts/start", json={
        "muscle_groups": ["Chest"],
        "notes": "Test workout"
    })
    assert response.status_code == 201
    assert response.json()["id"] is not None

def test_cannot_start_two_workouts(client):
    # Crear el primero
    client.post("/api/workouts/start", json={"muscle_groups": ["Chest"]})
    
    # Intentar crear otro
    response = client.post("/api/workouts/start", json={"muscle_groups": ["Back"]})
    assert response.status_code == 409