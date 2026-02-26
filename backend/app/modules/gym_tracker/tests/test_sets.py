class TestCreateSet:

    def test_create_weight_set_success(
        self, client, active_workout_id, weight_exercise_id, sample_set_weight_data
    ):
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json=sample_set_weight_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["exercise_id"] == weight_exercise_id
        assert data["set_number"] == 1
        assert data["weight_kg"] == 80.0
        assert data["reps"] == 10
        assert data["rpe"] == 7
        assert data["speed_kmh"] is None
        assert data["incline_percent"] is None
        assert data["duration_seconds"] is None

    def test_create_cardio_set_success(
        self, client, active_workout_id, cardio_exercise_id, sample_set_cardio_data
    ):
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
            json=sample_set_cardio_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["exercise_id"] == cardio_exercise_id
        assert data["set_number"] == 1
        assert data["speed_kmh"] == 12.0
        assert data["incline_percent"] == 5.0
        assert data["duration_seconds"] == 600
        assert data["weight_kg"] is None
        assert data["reps"] is None

    def test_create_multiple_sets_increments_set_number(
        self, client, active_workout_id, weight_exercise_id, sample_set_weight_data
    ):
        response1 = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json=sample_set_weight_data
        )
        assert response1.json()["set_number"] == 1

        response2 = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json={**sample_set_weight_data, "weight_kg": 85.0}
        )
        assert response2.json()["set_number"] == 2

        response3 = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json={**sample_set_weight_data, "weight_kg": 90.0}
        )
        assert response3.json()["set_number"] == 3

    def test_create_set_workout_not_found(
        self, client, weight_exercise_id, sample_set_weight_data
    ):
        response = client.post(
            f"/api/v1/workouts/999/{weight_exercise_id}/sets",
            json=sample_set_weight_data
        )
        assert response.status_code == 404

    def test_create_set_exercise_not_found(
        self, client, active_workout_id, sample_set_weight_data
    ):
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/999/sets",
            json=sample_set_weight_data
        )
        assert response.status_code == 404

    def test_create_set_exercise_not_in_workout(
        self, client, active_workout_id, sample_exercise_weight_data, sample_set_weight_data
    ):
        # Finalizar el workout activo
        client.post(f"/api/v1/workouts/{active_workout_id}", json={})

        # Crear segundo workout
        response2 = client.post("/api/v1/workouts/", json={
            "muscle_groups": ["Chest"],
            "notes": "Second workout"
        })
        workout2_id = response2.json()["id"]

        # Crear ejercicio en el segundo workout
        response3 = client.post(
            f"/api/v1/workouts/{workout2_id}/exercises",
            json=sample_exercise_weight_data
        )
        exercise2_id = response3.json()["id"]

        # Intentar crear set con workout_id del primero y exercise_id del segundo
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{exercise2_id}/sets",
            json=sample_set_weight_data
        )
        assert response.status_code == 409  # ExerciseNotInWorkoutError

    def test_create_weight_set_missing_required_fields(
        self, client, active_workout_id, weight_exercise_id
    ):
        invalid_data = {
            "rpe": 7,
            "notes": None,
            "speed_kmh": None,
            "incline_percent": None,
            "duration_seconds": None
        }
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json=invalid_data
        )
        assert response.status_code == 409  # SetTypeMismatchError

    def test_create_cardio_set_missing_required_fields(
        self, client, active_workout_id, cardio_exercise_id
    ):
        invalid_data = {
            "incline_percent": 5.0,
            "rpe": 6,
            "notes": None,
            "weight_kg": None,
            "reps": None
        }
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
            json=invalid_data
        )
        assert response.status_code == 409  # SetTypeMismatchError

    def test_create_weight_set_on_cardio_exercise(
        self, client, active_workout_id, cardio_exercise_id, sample_set_weight_data
    ):
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
            json=sample_set_weight_data
        )
        assert response.status_code == 409  # SetTypeMismatchError

    def test_create_cardio_set_on_weight_exercise(
        self, client, active_workout_id, weight_exercise_id, sample_set_cardio_data
    ):
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json=sample_set_cardio_data
        )
        assert response.status_code == 409  # SetTypeMismatchError


class TestGetSets:

    def test_get_sets_empty(self, client, active_workout_id, weight_exercise_id):
        response = client.get(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets"
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_get_sets_multiple(
        self, client, active_workout_id, weight_exercise_id, sample_set_weight_data
    ):
        for i in range(3):
            client.post(
                f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                json={**sample_set_weight_data, "weight_kg": 80.0 + (i * 5)}
            )

        response = client.get(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["set_number"] == 1
        assert data[1]["set_number"] == 2
        assert data[2]["set_number"] == 3
        assert data[0]["weight_kg"] == 80.0
        assert data[1]["weight_kg"] == 85.0
        assert data[2]["weight_kg"] == 90.0

    def test_get_sets_workout_not_found(self, client, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/999/{weight_exercise_id}/sets")
        assert response.status_code == 404

    def test_get_sets_exercise_not_found(self, client, active_workout_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/999/sets")
        assert response.status_code == 404


class TestDeleteSet:

    def test_delete_set_success(self, client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        response = client.delete(
            f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}"
        )
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets")
        assert len(get_response.json()) == 0

    def test_delete_set_not_found(
        self, client, active_workout_id, weight_exercise_id
    ):
        response = client.delete(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets/999"
        )
        assert response.status_code == 404

    def test_delete_set_workout_not_found(self, client, weight_exercise_with_set):
        _, exercise_id, set_id = weight_exercise_with_set
        response = client.delete(
            f"/api/v1/workouts/999/{exercise_id}/sets/{set_id}"
        )
        assert response.status_code == 404

    def test_delete_set_exercise_not_found(self, client, weight_exercise_with_set):
        workout_id, _, set_id = weight_exercise_with_set
        response = client.delete(
            f"/api/v1/workouts/{workout_id}/999/sets/{set_id}"
        )
        assert response.status_code == 404

    def test_delete_one_of_multiple_sets(
        self, client, active_workout_id, weight_exercise_id, sample_set_weight_data
    ):
        set_ids = []
        for i in range(3):
            response = client.post(
                f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                json={**sample_set_weight_data, "weight_kg": 80.0 + (i * 5)}
            )
            set_ids.append(response.json()["id"])

        client.delete(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets/{set_ids[1]}"
        )

        response = client.get(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets"
        )
        remaining_sets = response.json()
        assert len(remaining_sets) == 2
        assert remaining_sets[0]["id"] == set_ids[0]
        assert remaining_sets[1]["id"] == set_ids[2]


class TestSetEdgeCases:

    def test_create_set_with_rpe_boundaries(
        self, client, active_workout_id, weight_exercise_id
    ):
        response1 = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json={"weight_kg": 80.0, "reps": 10, "rpe": 1}
        )
        assert response1.status_code == 201

        response2 = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json={"weight_kg": 80.0, "reps": 10, "rpe": 10}
        )
        assert response2.status_code == 201

    def test_create_set_with_zero_weight(
        self, client, active_workout_id, weight_exercise_id
    ):
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json={"weight_kg": 0.0, "reps": 10, "rpe": 7}
        )
        assert response.status_code == 201
        assert response.json()["weight_kg"] == 0.0

    def test_create_set_with_notes(
        self, client, active_workout_id, weight_exercise_id, sample_set_weight_data
    ):
        data_with_notes = {**sample_set_weight_data, "notes": "Felt heavy"}
        response = client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json=data_with_notes
        )
        assert response.status_code == 201
        assert response.json()["notes"] == "Felt heavy"