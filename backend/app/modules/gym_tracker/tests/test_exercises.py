class TestCreateExercise:

    def test_create_weight_exercise_success(self, client, active_workout_id):
        data = {"name": "Bench Press", "exercise_type": "Weight_reps", "notes": "Wide grip"}
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["workout_id"] == active_workout_id
        assert body["name"] == "Bench Press"
        assert body["exercise_type"] == "Weight_reps"
        assert body["order"] == 1
        assert body["notes"] == "Wide grip"
        assert body["created_at"] is not None

    def test_create_cardio_exercise_success(self, client, active_workout_id):
        data = {"name": "Treadmill", "exercise_type": "Cardio"}
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["exercise_type"] == "Cardio"
        assert body["notes"] is None

    def test_create_exercise_order_increments(self, client, active_workout_id):
        r1 = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                        json={"name": "Squat", "exercise_type": "Weight_reps"})
        r2 = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                        json={"name": "Treadmill", "exercise_type": "Cardio"})
        r3 = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                        json={"name": "Deadlift", "exercise_type": "Weight_reps"})
        assert r1.json()["order"] == 1
        assert r2.json()["order"] == 2
        assert r3.json()["order"] == 3

    def test_create_exercise_name_normalized(self, client, active_workout_id):
        """El nombre se normaliza a title case"""
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                            json={"name": "bench press", "exercise_type": "Weight_reps"})
        assert response.status_code == 201
        assert response.json()["name"] == "Bench Press"

    def test_create_exercise_name_strips_whitespace(self, client, active_workout_id):
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                            json={"name": "  Squat  ", "exercise_type": "Weight_reps"})
        assert response.status_code == 201
        assert response.json()["name"] == "Squat"

    def test_create_exercise_without_notes(self, client, active_workout_id):
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                            json={"name": "Pull Up", "exercise_type": "Weight_reps"})
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_create_exercise_workout_not_found(self, client):
        response = client.post("/api/v1/workouts/99999/exercises",
                            json={"name": "Squat", "exercise_type": "Weight_reps"})
        assert response.status_code == 404

    def test_create_exercise_on_ended_workout_fails(self, client, ended_workout_id):
        """Regla de negocio: no se puede añadir ejercicio a workout terminado"""
        response = client.post(f"/api/v1/workouts/{ended_workout_id}/exercises",
                            json={"name": "Squat", "exercise_type": "Weight_reps"})
        assert response.status_code == 409

    def test_create_exercise_missing_name_fails(self, client, active_workout_id):
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                            json={"exercise_type": "Weight_reps"})
        assert response.status_code == 422

    def test_create_exercise_empty_name_fails(self, client, active_workout_id):
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                            json={"name": "", "exercise_type": "Weight_reps"})
        assert response.status_code == 422

    def test_create_exercise_missing_type_fails(self, client, active_workout_id):
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                            json={"name": "Squat"})
        assert response.status_code == 422

    def test_create_exercise_invalid_type_fails(self, client, active_workout_id):
        response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                            json={"name": "Squat", "exercise_type": "Yoga"})
        assert response.status_code == 422

    def test_create_multiple_exercises_same_workout(self, client, active_workout_id):
        for i in range(5):
            response = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                                json={"name": f"Exercise {i}", "exercise_type": "Weight_reps"})
            assert response.status_code == 201

        get_response = client.get(f"/api/v1/workouts/{active_workout_id}/exercises")
        assert len(get_response.json()) == 5


class TestGetExercises:

    def test_get_exercises_empty(self, client, active_workout_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/exercises")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_exercises_returns_list(self, client, active_workout_id, weight_exercise_id, cardio_exercise_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/exercises")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_exercises_ordered_by_order(self, client, active_workout_id):
        client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                    json={"name": "First", "exercise_type": "Weight_reps"})
        client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                    json={"name": "Second", "exercise_type": "Cardio"})
        client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                    json={"name": "Third", "exercise_type": "Weight_reps"})
        response = client.get(f"/api/v1/workouts/{active_workout_id}/exercises")
        exercises = response.json()
        assert exercises[0]["order"] == 1
        assert exercises[1]["order"] == 2
        assert exercises[2]["order"] == 3

    def test_get_exercises_workout_not_found(self, client):
        response = client.get("/api/v1/workouts/99999/exercises")
        assert response.status_code == 404

    def test_get_exercises_response_fields(self, client, active_workout_id, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/exercises")
        item = response.json()[0]
        assert "id" in item
        assert "workout_id" in item
        assert "name" in item
        assert "exercise_type" in item
        assert "order" in item
        assert "notes" in item
        assert "created_at" in item

    def test_get_exercises_does_not_include_sets(self, client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        response = client.get(f"/api/v1/workouts/{workout_id}/exercises")
        item = response.json()[0]
        assert "sets" not in item


class TestGetExerciseById:

    def test_get_exercise_success(self, client, active_workout_id, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}")
        assert response.status_code == 200
        assert response.json()["id"] == weight_exercise_id

    def test_get_exercise_not_found(self, client, active_workout_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/99999")
        assert response.status_code == 404

    def test_get_exercise_workout_not_found(self, client, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/99999/{weight_exercise_id}")
        assert response.status_code == 404

    def test_get_exercise_not_in_workout_fails(self, client, active_workout_id, sample_exercise_weight_data):
        """Regla de negocio: el ejercicio debe pertenecer al workout"""
        # Terminar workout actual y crear otro
        client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        r2 = client.post("/api/v1/workouts/", json={"muscle_groups": ["Legs"]})
        workout2_id = r2.json()["id"]
        r3 = client.post(f"/api/v1/workouts/{workout2_id}/exercises",
                        json=sample_exercise_weight_data)
        exercise2_id = r3.json()["id"]

        # Intentar obtener ejercicio del workout2 usando workout_id del primero
        response = client.get(f"/api/v1/workouts/{active_workout_id}/{exercise2_id}")
        assert response.status_code == 409

    def test_get_exercise_response_fields(self, client, active_workout_id, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}")
        body = response.json()
        assert "id" in body
        assert "workout_id" in body
        assert "name" in body
        assert "exercise_type" in body
        assert "order" in body
        assert "notes" in body
        assert "created_at" in body


class TestGetExerciseLong:

    def test_get_exercise_long_success(self, client, active_workout_id, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/long")
        assert response.status_code == 200

    def test_get_exercise_long_includes_sets(self, client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        response = client.get(f"/api/v1/workouts/{workout_id}/{exercise_id}/long")
        body = response.json()
        assert "sets" in body
        assert len(body["sets"]) == 1
        assert body["sets"][0]["id"] == set_id

    def test_get_exercise_long_empty_sets(self, client, active_workout_id, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/long")
        assert response.json()["sets"] == []

    def test_get_exercise_long_multiple_sets(self, client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        for i in range(3):
            client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                        json={**sample_set_weight_data, "weight_kg": 80.0 + i * 5})
        response = client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/long")
        assert len(response.json()["sets"]) == 3

    def test_get_exercise_long_not_found(self, client, active_workout_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/99999/long")
        assert response.status_code == 404

    def test_get_exercise_long_workout_not_found(self, client, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/99999/{weight_exercise_id}/long")
        assert response.status_code == 404


class TestDeleteExercise:

    def test_delete_exercise_success(self, client, active_workout_id, weight_exercise_id):
        response = client.delete(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}")
        assert response.status_code == 204

    def test_delete_exercise_removes_it(self, client, active_workout_id, weight_exercise_id):
        client.delete(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}")
        response = client.get(f"/api/v1/workouts/{active_workout_id}/exercises")
        assert len(response.json()) == 0

    def test_delete_exercise_not_found(self, client, active_workout_id):
        response = client.delete(f"/api/v1/workouts/{active_workout_id}/99999")
        assert response.status_code == 404

    def test_delete_exercise_workout_not_found(self, client, weight_exercise_id):
        response = client.delete(f"/api/v1/workouts/99999/{weight_exercise_id}")
        assert response.status_code == 404

    def test_delete_exercise_cascades_sets(self, client, weight_exercise_with_set):
        """Regla de negocio: al eliminar ejercicio se eliminan sus series"""
        workout_id, exercise_id, set_id = weight_exercise_with_set
        client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}")
        # El ejercicio ya no existe, no deberían quedar sets
        get_response = client.get(f"/api/v1/workouts/{workout_id}/exercises")
        assert len(get_response.json()) == 0

    def test_delete_one_exercise_preserves_others(self, client, active_workout_id):
        r1 = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                        json={"name": "Squat", "exercise_type": "Weight_reps"})
        r2 = client.post(f"/api/v1/workouts/{active_workout_id}/exercises",
                        json={"name": "Deadlift", "exercise_type": "Weight_reps"})
        ex1_id = r1.json()["id"]
        ex2_id = r2.json()["id"]

        client.delete(f"/api/v1/workouts/{active_workout_id}/{ex1_id}")
        response = client.get(f"/api/v1/workouts/{active_workout_id}/exercises")
        remaining = response.json()
        assert len(remaining) == 1
        assert remaining[0]["id"] == ex2_id

    def test_delete_exercise_not_in_workout_fails(self, client, active_workout_id, sample_exercise_weight_data):
        client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        r2 = client.post("/api/v1/workouts/", json={"muscle_groups": ["Back"]})
        workout2_id = r2.json()["id"]
        r3 = client.post(f"/api/v1/workouts/{workout2_id}/exercises", json=sample_exercise_weight_data)
        exercise2_id = r3.json()["id"]

        response = client.delete(f"/api/v1/workouts/{active_workout_id}/{exercise2_id}")
        assert response.status_code == 409