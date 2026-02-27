class TestAuth:

    def test_get_workouts_without_token_fails(self, client):
        response = client.get("/api/v1/workouts/")
        assert response.status_code == 401

    def test_create_workout_without_token_fails(self, client):
        response = client.post("/api/v1/workouts/", json={"muscle_groups": ["Chest"]})
        assert response.status_code == 401

    def test_get_workout_by_id_without_token_fails(self, client, auth_client, active_workout_id):
        response = client.get(f"/api/v1/workouts/{active_workout_id}")
        assert response.status_code == 401

    def test_delete_workout_without_token_fails(self, client, auth_client, active_workout_id):
        response = client.delete(f"/api/v1/workouts/{active_workout_id}")
        assert response.status_code == 401


class TestOwnership:

    def test_cannot_get_other_users_workout(self, auth_client, other_auth_client, active_workout_id):
        response = other_auth_client.get(f"/api/v1/workouts/{active_workout_id}")
        assert response.status_code == 404

    def test_cannot_end_other_users_workout(self, auth_client, other_auth_client, active_workout_id):
        response = other_auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        assert response.status_code == 404

    def test_cannot_delete_other_users_workout(self, auth_client, other_auth_client, active_workout_id):
        response = other_auth_client.delete(f"/api/v1/workouts/{active_workout_id}")
        assert response.status_code == 404

    def test_users_see_only_their_workouts(self, auth_client, other_auth_client, active_workout_id):
        other_auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Back"]})
        response = auth_client.get("/api/v1/workouts/")
        assert len(response.json()) == 1

    def test_other_user_can_have_active_workout_simultaneously(self, auth_client, other_auth_client, active_workout_id):
        """El límite de workout activo es por usuario, no global"""
        response = other_auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Legs"]})
        assert response.status_code == 201

    def test_other_user_workouts_not_in_list(self, auth_client, other_auth_client):
        other_auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Back"]})
        response = auth_client.get("/api/v1/workouts/")
        assert response.json() == []


class TestGetWorkouts:

    def test_get_workouts_empty(self, auth_client):
        response = auth_client.get("/api/v1/workouts/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_workouts_returns_list(self, auth_client, ended_workout_id):
        response = auth_client.get("/api/v1/workouts/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_workouts_multiple(self, auth_client):
        auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Chest"], "notes": "W1"})
        first_id = auth_client.get("/api/v1/workouts/").json()[0]["id"]
        auth_client.post(f"/api/v1/workouts/{first_id}", json={"notes": "done"})
        auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Back"], "notes": "W2"})
        second_id = auth_client.get("/api/v1/workouts/").json()[1]["id"]
        auth_client.post(f"/api/v1/workouts/{second_id}", json={})
        response = auth_client.get("/api/v1/workouts/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_workouts_response_fields(self, auth_client, ended_workout_id):
        response = auth_client.get("/api/v1/workouts/")
        item = response.json()[0]
        assert "id" in item
        assert "started_at" in item
        assert "ended_at" in item
        assert "duration_minutes" in item
        assert "total_exercises" in item
        assert "total_sets" in item
        assert "notes" in item

    def test_get_workouts_does_not_include_exercises(self, auth_client, ended_workout_id):
        response = auth_client.get("/api/v1/workouts/")
        item = response.json()[0]
        assert "exercises" not in item


class TestCreateWorkout:

    def test_create_workout_success(self, auth_client):
        data = {"muscle_groups": ["Chest", "Back"], "notes": "Test"}
        response = auth_client.post("/api/v1/workouts/", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["started_at"] is not None
        assert body["ended_at"] is None
        assert body["duration_minutes"] is None
        assert body["total_exercises"] is None
        assert body["total_sets"] is None
        assert body["notes"] == "Test"

    def test_create_workout_all_muscle_groups(self, auth_client):
        muscle_groups = ["Chest", "Back", "Biceps", "Triceps", "Core", "Abs", "Shoulders", "Legs"]
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": muscle_groups})
        assert response.status_code == 201

    def test_create_workout_single_muscle_group(self, auth_client):
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Chest"]})
        assert response.status_code == 201

    def test_create_workout_without_notes(self, auth_client):
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Legs"]})
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_create_workout_with_notes(self, auth_client):
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Core"], "notes": "Heavy day"})
        assert response.status_code == 201
        assert response.json()["notes"] == "Heavy day"

    def test_create_workout_missing_muscle_groups_fails(self, auth_client):
        response = auth_client.post("/api/v1/workouts/", json={"notes": "No muscles"})
        assert response.status_code == 422

    def test_create_workout_empty_muscle_groups_fails(self, auth_client):
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": []})
        assert response.status_code == 422

    def test_create_workout_invalid_muscle_group_fails(self, auth_client):
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["InvalidMuscle"]})
        assert response.status_code == 422

    def test_create_workout_when_active_exists_fails(self, auth_client, active_workout_id):
        """Solo un workout activo a la vez por usuario"""
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Back"]})
        assert response.status_code == 409

    def test_create_workout_after_ending_previous_succeeds(self, auth_client, active_workout_id):
        auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Legs"]})
        assert response.status_code == 201

    def test_create_workout_ids_increment(self, auth_client):
        r1 = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Chest"]})
        id1 = r1.json()["id"]
        auth_client.post(f"/api/v1/workouts/{id1}", json={})
        r2 = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Back"]})
        assert r2.json()["id"] > id1


class TestGetWorkoutById:

    def test_get_workout_success(self, auth_client, active_workout_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}")
        assert response.status_code == 200
        assert response.json()["id"] == active_workout_id

    def test_get_workout_not_found(self, auth_client):
        response = auth_client.get("/api/v1/workouts/99999")
        assert response.status_code == 404

    def test_get_workout_response_fields(self, auth_client, active_workout_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}")
        body = response.json()
        assert "id" in body
        assert "started_at" in body
        assert "ended_at" in body
        assert "duration_minutes" in body
        assert "total_exercises" in body
        assert "total_sets" in body
        assert "notes" in body

    def test_get_active_workout_has_no_ended_at(self, auth_client, active_workout_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}")
        assert response.json()["ended_at"] is None


class TestGetWorkoutLong:

    def test_get_workout_long_success(self, auth_client, active_workout_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/long")
        assert response.status_code == 200

    def test_get_workout_long_includes_exercises(self, auth_client, active_workout_id, weight_exercise_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/long")
        body = response.json()
        assert "exercises" in body
        assert len(body["exercises"]) == 1

    def test_get_workout_long_includes_sets(self, auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        response = auth_client.get(f"/api/v1/workouts/{workout_id}/long")
        exercises = response.json()["exercises"]
        assert len(exercises[0]["sets"]) == 1

    def test_get_workout_long_empty_exercises(self, auth_client, active_workout_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/long")
        assert response.json()["exercises"] == []

    def test_get_workout_long_not_found(self, auth_client):
        response = auth_client.get("/api/v1/workouts/99999/long")
        assert response.status_code == 404

    def test_get_workout_long_muscle_groups_included(self, auth_client, active_workout_id):
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/long")
        body = response.json()
        assert "muscle_groups" in body
        assert len(body["muscle_groups"]) > 0


class TestEndWorkout:

    def test_end_workout_success(self, auth_client, active_workout_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={"notes": "Good session"})
        assert response.status_code == 201
        body = response.json()
        assert body["ended_at"] is not None
        assert body["notes"] == "Good session"

    def test_end_workout_calculates_duration(self, auth_client, active_workout_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        body = response.json()
        assert body["duration_minutes"] is not None
        assert body["duration_minutes"] >= 0

    def test_end_workout_calculates_total_exercises(self, auth_client, active_workout_id, weight_exercise_id, cardio_exercise_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        assert response.json()["total_exercises"] == 2

    def test_end_workout_calculates_total_sets(self, auth_client, weight_exercise_with_set):
        workout_id, exercise_id, set_id = weight_exercise_with_set
        auth_client.post(f"/api/v1/workouts/{workout_id}/{exercise_id}/sets",
                         json={"weight_kg": 85.0, "reps": 8, "rpe": 8})
        response = auth_client.post(f"/api/v1/workouts/{workout_id}", json={})
        assert response.json()["total_sets"] == 2

    def test_end_workout_no_exercises_total_is_zero(self, auth_client, active_workout_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        assert response.json()["total_exercises"] == 0
        assert response.json()["total_sets"] == 0

    def test_end_workout_without_notes(self, auth_client, active_workout_id):
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        assert response.status_code == 201

    def test_end_workout_not_found(self, auth_client):
        response = auth_client.post("/api/v1/workouts/99999", json={})
        assert response.status_code == 404

    def test_end_already_ended_workout_fails(self, auth_client, active_workout_id):
        auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        response = auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        assert response.status_code == 409

    def test_end_workout_allows_new_workout(self, auth_client, active_workout_id):
        auth_client.post(f"/api/v1/workouts/{active_workout_id}", json={})
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Legs"]})
        assert response.status_code == 201


class TestDeleteWorkout:

    def test_delete_workout_success(self, auth_client, active_workout_id):
        response = auth_client.delete(f"/api/v1/workouts/{active_workout_id}")
        assert response.status_code == 204

    def test_delete_workout_not_found(self, auth_client):
        response = auth_client.delete("/api/v1/workouts/99999")
        assert response.status_code == 404

    def test_delete_workout_removes_it(self, auth_client, active_workout_id):
        auth_client.delete(f"/api/v1/workouts/{active_workout_id}")
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}")
        assert response.status_code == 404

    def test_delete_workout_cascades_exercises(self, auth_client, active_workout_id, weight_exercise_id):
        auth_client.delete(f"/api/v1/workouts/{active_workout_id}")
        response = auth_client.get(f"/api/v1/workouts/{active_workout_id}/exercises")
        assert response.status_code == 404

    def test_delete_workout_allows_new_active(self, auth_client, active_workout_id):
        auth_client.delete(f"/api/v1/workouts/{active_workout_id}")
        response = auth_client.post("/api/v1/workouts/", json={"muscle_groups": ["Back"]})
        assert response.status_code == 201

    def test_delete_ended_workout_success(self, auth_client, ended_workout_id):
        response = auth_client.delete(f"/api/v1/workouts/{ended_workout_id}")
        assert response.status_code == 204