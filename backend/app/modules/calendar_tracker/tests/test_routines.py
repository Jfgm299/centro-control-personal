import pytest
from datetime import date


class TestRoutinesAuth:

    def test_list_without_token_fails(self, client):
        assert client.get("/api/v1/calendar/routines").status_code == 401

    def test_create_without_token_fails(self, client):
        assert client.post("/api/v1/calendar/routines", json={}).status_code == 401


class TestRoutinesOwnership:

    def test_users_see_only_their_routines(self, auth_client, other_auth_client, routine_id):
        ids = [r["id"] for r in other_auth_client.get("/api/v1/calendar/routines").json()]
        assert routine_id not in ids

    def test_cannot_update_other_users_routine(self, auth_client, other_auth_client, routine_id):
        assert other_auth_client.put(
            f"/api/v1/calendar/routines/{routine_id}", json={"title": "Hack"}
        ).status_code == 404

    def test_cannot_delete_other_users_routine(self, auth_client, other_auth_client, routine_id):
        assert other_auth_client.delete(
            f"/api/v1/calendar/routines/{routine_id}"
        ).status_code == 404


class TestCreateRoutine:

    def test_create_success(self, auth_client, routine_data):
        response = auth_client.post("/api/v1/calendar/routines", json=routine_data)
        assert response.status_code == 201
        body = response.json()
        assert body["title"]      == routine_data["title"]
        assert body["rrule"]      == routine_data["rrule"]
        assert body["is_active"]  is True
        assert body["enable_dnd"] is False

    def test_create_with_dnd_and_reminder(self, auth_client, routine_data):
        data = {**routine_data, "title": "Gym DND", "enable_dnd": True, "reminder_minutes": 15}
        response = auth_client.post("/api/v1/calendar/routines", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["enable_dnd"]       is True
        assert body["reminder_minutes"] == 15

    def test_create_end_time_before_start_fails(self, auth_client, routine_data):
        data = {**routine_data, "start_time": "20:00:00", "end_time": "18:00:00"}
        assert auth_client.post("/api/v1/calendar/routines", json=data).status_code == 422

    def test_create_valid_until_before_valid_from_fails(self, auth_client, routine_data):
        data = {**routine_data, "valid_from": "2026-06-01", "valid_until": "2026-01-01"}
        assert auth_client.post("/api/v1/calendar/routines", json=data).status_code == 422

    def test_create_with_valid_until(self, auth_client, routine_data):
        data = {**routine_data, "valid_until": "2026-12-31"}
        response = auth_client.post("/api/v1/calendar/routines", json=data)
        assert response.status_code == 201
        assert response.json()["valid_until"] == "2026-12-31"


class TestUpdateRoutine:

    def test_update_title(self, auth_client, routine_id):
        response = auth_client.put(
            f"/api/v1/calendar/routines/{routine_id}", json={"title": "Gym Actualizado"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Gym Actualizado"

    def test_update_enable_dnd(self, auth_client, routine_id):
        response = auth_client.put(
            f"/api/v1/calendar/routines/{routine_id}", json={"enable_dnd": True}
        )
        assert response.status_code == 200
        assert response.json()["enable_dnd"] is True

    def test_deactivate_routine(self, auth_client, routine_id):
        response = auth_client.put(
            f"/api/v1/calendar/routines/{routine_id}", json={"is_active": False}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_nonexistent_fails(self, auth_client):
        assert auth_client.put(
            "/api/v1/calendar/routines/99999", json={"title": "X"}
        ).status_code == 404


class TestDeleteRoutine:

    def test_delete_success(self, auth_client, routine_id):
        assert auth_client.delete(
            f"/api/v1/calendar/routines/{routine_id}"
        ).status_code == 204

    def test_delete_removes_from_list(self, auth_client, routine_id):
        auth_client.delete(f"/api/v1/calendar/routines/{routine_id}")
        ids = [r["id"] for r in auth_client.get("/api/v1/calendar/routines").json()]
        assert routine_id not in ids

    def test_delete_nonexistent_fails(self, auth_client):
        assert auth_client.delete(
            "/api/v1/calendar/routines/99999"
        ).status_code == 404


class TestRoutineExceptions:

    def test_cancel_instance(self, auth_client, routine_id):
        response = auth_client.post(
            f"/api/v1/calendar/routines/{routine_id}/exceptions",
            json={"original_date": "2026-03-09", "action": "cancelled"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["action"]        == "cancelled"
        assert body["original_date"] == "2026-03-09"

    def test_modify_instance(self, auth_client, routine_id):
        response = auth_client.post(
            f"/api/v1/calendar/routines/{routine_id}/exceptions",
            json={
                "original_date": "2026-03-16",
                "action":        "modified",
                "new_start_at":  "2026-03-16T19:00:00+00:00",
                "new_end_at":    "2026-03-16T21:00:00+00:00",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["action"]       == "modified"
        assert body["new_start_at"] is not None

    def test_duplicate_exception_fails(self, auth_client, routine_id):
        payload = {"original_date": "2026-03-23", "action": "cancelled"}
        auth_client.post(f"/api/v1/calendar/routines/{routine_id}/exceptions", json=payload)
        assert auth_client.post(
            f"/api/v1/calendar/routines/{routine_id}/exceptions", json=payload
        ).status_code == 409

    def test_exception_on_nonexistent_routine_fails(self, auth_client):
        assert auth_client.post(
            "/api/v1/calendar/routines/99999/exceptions",
            json={"original_date": "2026-03-09", "action": "cancelled"},
        ).status_code == 404

    def test_modify_with_end_before_start_fails(self, auth_client, routine_id):
        assert auth_client.post(
            f"/api/v1/calendar/routines/{routine_id}/exceptions",
            json={
                "original_date": "2026-03-30",
                "action":        "modified",
                "new_start_at":  "2026-03-30T20:00:00+00:00",
                "new_end_at":    "2026-03-30T18:00:00+00:00",
            },
        ).status_code == 422