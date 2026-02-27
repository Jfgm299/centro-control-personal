class TestAuth:

    def test_create_set_without_token_fails(self, client, auth_client, active_workout_id, weight_exercise_id):
        response = client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                               json={"weight_kg": 80.0, "reps": 10})
        assert response.status_code == 401

    def test_get_sets_without_token_fails(self, client, auth_client, active_workout_id, weight_exercise_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets")
        assert response.status_code == 401

    def test_delete_set_without_token_fails(self, client, auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        response = client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}")
        assert response.status_code == 401


class TestOwnership:

    def test_cannot_create_set_in_other_users_workout(self, auth_client, other_auth_client, active_workout_id, weight_exercise_id):
        response = other_auth_client.post(
            f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
            json={"weight_kg": 80.0, "reps": 10}
        )
        assert response.status_code == 403

    def test_cannot_get_sets_of_other_users_workout(self, auth_client, other_auth_client, active_workout_id, weight_exercise_id):
        response = other_auth_client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets")
        assert response.status_code == 403

    def test_cannot_delete_set_of_other_users_workout(self, auth_client, other_auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        response = other_auth_client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}")
        assert response.status_code == 403


class TestCreateSet:

    def test_create_weight_set_success(self, auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        response = auth_client.post(
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
        assert data["created_at"] is not None

    def test_create_cardio_set_success(self, auth_client, active_workout_id, cardio_exercise_id, sample_set_cardio_data):
        response = auth_client.post(
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

    def test_create_multiple_sets_increments_set_number(self, auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        r1 = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets", json=sample_set_weight_data)
        assert r1.json()["set_number"] == 1
        r2 = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                               json={**sample_set_weight_data, "weight_kg": 85.0})
        assert r2.json()["set_number"] == 2
        r3 = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                               json={**sample_set_weight_data, "weight_kg": 90.0})
        assert r3.json()["set_number"] == 3

    def test_set_numbers_independent_per_exercise(self, auth_client, active_workout_id, weight_exercise_id, cardio_exercise_id, sample_set_weight_data, sample_set_cardio_data):
        auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets", json=sample_set_weight_data)
        auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets", json=sample_set_weight_data)
        r = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets", json=sample_set_cardio_data)
        assert r.json()["set_number"] == 1

    def test_create_set_workout_not_found(self, auth_client, weight_exercise_id, sample_set_weight_data):
        response = auth_client.post(f"/api/v1/workouts/999/{weight_exercise_id}/sets", json=sample_set_weight_data)
        assert response.status_code == 404

    def test_create_set_exercise_not_found(self, auth_client, active_workout_id, sample_set_weight_data):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/999/sets", json=sample_set_weight_data)
        assert response.status_code == 404

    def test_create_set_exercise_not_in_workout(self, auth_client, active_workout_id, sample_exercise_weight_data, sample_set_weight_data):
        auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        r2 = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Chest"]})
        workout2_id = r2.json()["id"]
        r3 = auth_client.post(f"/api/v1/workouts/{workout2_id}/exercises", json=sample_exercise_weight_data)
        exercise2_id = r3.json()["id"]
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{exercise2_id}/sets", json=sample_set_weight_data)
        assert response.status_code == 409

    def test_create_weight_set_on_cardio_exercise_fails(self, auth_client, active_workout_id, cardio_exercise_id, sample_set_weight_data):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets", json=sample_set_weight_data)
        assert response.status_code == 409

    def test_create_cardio_set_on_weight_exercise_fails(self, auth_client, active_workout_id, weight_exercise_id, sample_set_cardio_data):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets", json=sample_set_cardio_data)
        assert response.status_code == 409

    def test_create_weight_set_missing_weight_and_reps_fails(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"rpe": 7})
        assert response.status_code == 409

    def test_create_cardio_set_missing_speed_and_duration_fails(self, auth_client, active_workout_id, cardio_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
                                    json={"incline_percent": 5.0, "rpe": 6})
        assert response.status_code == 409

    def test_create_set_rpe_min_boundary(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"weight_kg": 80.0, "reps": 10, "rpe": 1})
        assert response.status_code == 201
        assert response.json()["rpe"] == 1

    def test_create_set_rpe_max_boundary(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"weight_kg": 80.0, "reps": 10, "rpe": 10})
        assert response.status_code == 201
        assert response.json()["rpe"] == 10

    def test_create_set_rpe_below_min_fails(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"weight_kg": 80.0, "reps": 10, "rpe": 0})
        assert response.status_code == 422

    def test_create_set_rpe_above_max_fails(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"weight_kg": 80.0, "reps": 10, "rpe": 11})
        assert response.status_code == 422

    def test_create_set_zero_weight_allowed(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"weight_kg": 0.0, "reps": 10})
        assert response.status_code == 201
        assert response.json()["weight_kg"] == 0.0

    def test_create_set_negative_weight_fails(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"weight_kg": -5.0, "reps": 10})
        assert response.status_code == 422

    def test_create_set_zero_reps_fails(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"weight_kg": 80.0, "reps": 0})
        assert response.status_code == 422

    def test_create_set_zero_speed_fails(self, auth_client, active_workout_id, cardio_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
                                    json={"speed_kmh": 0.0, "duration_seconds": 600})
        assert response.status_code == 422

    def test_create_set_zero_duration_fails(self, auth_client, active_workout_id, cardio_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
                                    json={"speed_kmh": 10.0, "duration_seconds": 0})
        assert response.status_code == 422

    def test_create_set_incline_min_boundary(self, auth_client, active_workout_id, cardio_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
                                    json={"speed_kmh": 10.0, "duration_seconds": 600, "incline_percent": 0.0})
        assert response.status_code == 201

    def test_create_set_incline_max_boundary(self, auth_client, active_workout_id, cardio_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
                                    json={"speed_kmh": 10.0, "duration_seconds": 600, "incline_percent": 100.0})
        assert response.status_code == 201

    def test_create_set_incline_above_max_fails(self, auth_client, active_workout_id, cardio_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
                                    json={"speed_kmh": 10.0, "duration_seconds": 600, "incline_percent": 101.0})
        assert response.status_code == 422

    def test_create_set_with_notes(self, auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        data = {**sample_set_weight_data, "notes": "Felt heavy today"}
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets", json=data)
        assert response.status_code == 201
        assert response.json()["notes"] == "Felt heavy today"

    def test_create_set_without_rpe(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                    json={"weight_kg": 80.0, "reps": 10})
        assert response.status_code == 201
        assert response.json()["rpe"] is None

    def test_create_cardio_set_without_incline(self, auth_client, active_workout_id, cardio_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets",
                                    json={"speed_kmh": 10.0, "duration_seconds": 600})
        assert response.status_code == 201
        assert response.json()["incline_percent"] is None


class TestGetSets:

    def test_get_sets_empty(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_sets_multiple(self, auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        for i in range(3):
            auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                             json={**sample_set_weight_data, "weight_kg": 80.0 + i * 5})
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["set_number"] == 1
        assert data[1]["set_number"] == 2
        assert data[2]["set_number"] == 3

    def test_get_sets_correct_weights(self, auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                         json={**sample_set_weight_data, "weight_kg": 80.0})
        auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                         json={**sample_set_weight_data, "weight_kg": 85.0})
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets")
        data = response.json()
        assert data[0]["weight_kg"] == 80.0
        assert data[1]["weight_kg"] == 85.0

    def test_get_sets_workout_not_found(self, auth_client, weight_exercise_id):
        response = auth_client.get(f"/api/v1/workouts/999/{weight_exercise_id}/sets")
        assert response.status_code == 404

    def test_get_sets_exercise_not_found(self, auth_client, active_workout_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/999/sets")
        assert response.status_code == 404

    def test_get_sets_response_fields(self, auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        response = auth_client.get(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets")
        item = response.json()[0]
        assert "id" in item
        assert "exercise_id" in item
        assert "set_number" in item
        assert "weight_kg" in item
        assert "reps" in item
        assert "speed_kmh" in item
        assert "incline_percent" in item
        assert "duration_seconds" in item
        assert "rpe" in item
        assert "notes" in item
        assert "created_at" in item

    def test_get_sets_only_for_correct_exercise(self, auth_client, active_workout_id, weight_exercise_id, cardio_exercise_id, sample_set_weight_data, sample_set_cardio_data):
        auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets", json=sample_set_weight_data)
        auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets", json=sample_set_weight_data)
        auth_client.post(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets", json=sample_set_cardio_data)
        weight_sets = auth_client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets").json()
        cardio_sets = auth_client.get(f"/api/v1/workouts/{active_workout_id}/{cardio_exercise_id}/sets").json()
        assert len(weight_sets) == 2
        assert len(cardio_sets) == 1


class TestDeleteSet:

    def test_delete_set_success(self, auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        response = auth_client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}")
        assert response.status_code == 204

    def test_delete_set_removes_it(self, auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        auth_client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}")
        response = auth_client.get(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets")
        assert len(response.json()) == 0

    def test_delete_set_not_found(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.delete(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets/99999")
        assert response.status_code == 404

    def test_delete_set_workout_not_found(self, auth_client, weight_exercise_with_set):
        _, exercise_id, set_id = weight_exercise_with_set
        response = auth_client.delete(f"/api/v1/workouts/999/{exercise_id}/sets/{set_id}")
        assert response.status_code == 404

    def test_delete_set_exercise_not_found(self, auth_client, weight_exercise_with_set):
        workout_id, _, set_id = weight_exercise_with_set
        response = auth_client.delete(f"/api/v1/workouts/{workout_id}/999/sets/{set_id}")
        assert response.status_code == 404

    def test_delete_middle_set_preserves_others(self, auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        set_ids = []
        for i in range(3):
            r = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                 json={**sample_set_weight_data, "weight_kg": 80.0 + i * 5})
            set_ids.append(r.json()["id"])
        auth_client.delete(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets/{set_ids[1]}")
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets")
        remaining = response.json()
        assert len(remaining) == 2
        assert remaining[0]["id"] == set_ids[0]
        assert remaining[1]["id"] == set_ids[2]

    def test_delete_first_set_preserves_others(self, auth_client, active_workout_id, weight_exercise_id, sample_set_weight_data):
        set_ids = []
        for i in range(3):
            r = auth_client.post(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets",
                                 json={**sample_set_weight_data, "weight_kg": 80.0 + i * 5})
            set_ids.append(r.json()["id"])
        auth_client.delete(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets/{set_ids[0]}")
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/{weight_exercise_id}/sets")
        assert len(response.json()) == 2

    def test_delete_set_twice_fails(self, auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        auth_client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}")
        response = auth_client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}")
        assert response.status_code == 404

    def test_delete_all_sets_exercise_still_exists(self, auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        auth_client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}")
        response = auth_client.get(f"/api/v1/workouts/{workout_id}/{exercise_id}")
        assert response.status_code == 200

    def test_delete_cardio_set_success(self, auth_client, cardio_exercise_with_set):
        workout_id, exercise_id, set_id = cardio_exercise_with_set
        response = auth_client.delete(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets/{set_id}")
        assert response.status_code == 204