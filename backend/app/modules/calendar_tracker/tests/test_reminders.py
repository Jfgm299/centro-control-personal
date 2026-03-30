import pytest
from datetime import datetime, timezone, timedelta


class TestRemindersAuth:

    def test_list_without_token_fails(self, client):
        assert client.get("/api/v1/calendar/reminders").status_code == 401

    def test_create_without_token_fails(self, client):
        assert client.post("/api/v1/calendar/reminders", json={}).status_code == 401


class TestRemindersOwnership:

    def test_users_see_only_their_reminders(self, auth_client, other_auth_client, reminder_id):
        ids = [r["id"] for r in other_auth_client.get("/api/v1/calendar/reminders").json()]
        assert reminder_id not in ids

    def test_cannot_update_other_users_reminder(self, auth_client, other_auth_client, reminder_id):
        assert other_auth_client.patch(
            f"/api/v1/calendar/reminders/{reminder_id}", json={"title": "Hack"}
        ).status_code == 404

    def test_cannot_delete_other_users_reminder(self, auth_client, other_auth_client, reminder_id):
        assert other_auth_client.delete(
            f"/api/v1/calendar/reminders/{reminder_id}"
        ).status_code == 404


class TestCreateReminder:

    def test_create_success(self, auth_client, reminder_data):
        response = auth_client.post("/api/v1/calendar/reminders", json=reminder_data)
        assert response.status_code == 201
        body = response.json()
        assert body["title"]    == reminder_data["title"]
        assert body["status"]   == "pending"
        assert body["priority"] == "medium"

    def test_create_empty_title_fails(self, auth_client):
        assert auth_client.post(
            "/api/v1/calendar/reminders", json={"title": ""}
        ).status_code == 422

    def test_create_invalid_priority_fails(self, auth_client):
        assert auth_client.post(
            "/api/v1/calendar/reminders",
            json={"title": "Test", "priority": "critical"},
        ).status_code == 422

    def test_create_all_priorities(self, auth_client):
        for priority in ["low", "medium", "high", "urgent"]:
            response = auth_client.post("/api/v1/calendar/reminders", json={
                "title": f"Reminder {priority}", "priority": priority,
            })
            assert response.status_code == 201, f"priority '{priority}' fallo"

    def test_create_with_due_date(self, auth_client):
        response = auth_client.post("/api/v1/calendar/reminders", json={
            "title": "Con fecha limite",
            "priority": "high",
            "due_date": "2026-12-31",
        })
        assert response.status_code == 201
        assert response.json()["due_date"] == "2026-12-31"

    def test_create_with_category(self, auth_client, category_id):
        response = auth_client.post("/api/v1/calendar/reminders", json={
            "title": "Con categoria",
            "category_id": category_id,
        })
        assert response.status_code == 201
        assert response.json()["category_id"] == category_id


class TestUpdateReminder:

    def test_update_title(self, auth_client, reminder_id):
        response = auth_client.patch(
            f"/api/v1/calendar/reminders/{reminder_id}",
            json={"title": "Comprar pan"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Comprar pan"

    def test_update_priority(self, auth_client, reminder_id):
        response = auth_client.patch(
            f"/api/v1/calendar/reminders/{reminder_id}",
            json={"priority": "urgent"},
        )
        assert response.status_code == 200
        assert response.json()["priority"] == "urgent"

    def test_update_nonexistent_fails(self, auth_client):
        assert auth_client.patch(
            "/api/v1/calendar/reminders/99999", json={"title": "X"}
        ).status_code == 404

    def test_update_status_to_done(self, auth_client, reminder_id):
        response = auth_client.patch(
            f"/api/v1/calendar/reminders/{reminder_id}",
            json={"status": "done"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "done"

    def test_update_status_to_pending(self, auth_client, reminder_id):
        auth_client.patch(f"/api/v1/calendar/reminders/{reminder_id}", json={"status": "done"})
        response = auth_client.patch(
            f"/api/v1/calendar/reminders/{reminder_id}",
            json={"status": "pending"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

    def test_update_status_invalid_fails(self, auth_client, reminder_id):
        assert auth_client.patch(
            f"/api/v1/calendar/reminders/{reminder_id}",
            json={"status": "completed"},
        ).status_code == 422

    def test_done_reminder_excluded_from_pending_filter(self, auth_client, reminder_id):
        auth_client.patch(f"/api/v1/calendar/reminders/{reminder_id}", json={"status": "done"})
        ids = [r["id"] for r in auth_client.get("/api/v1/calendar/reminders?status=pending").json()]
        assert reminder_id not in ids


class TestDeleteReminder:

    def test_delete_success(self, auth_client, reminder_id):
        assert auth_client.delete(
            f"/api/v1/calendar/reminders/{reminder_id}"
        ).status_code == 204

    def test_delete_removes_from_list(self, auth_client, reminder_id):
        auth_client.delete(f"/api/v1/calendar/reminders/{reminder_id}")
        ids = [r["id"] for r in auth_client.get("/api/v1/calendar/reminders").json()]
        assert reminder_id not in ids

    def test_delete_nonexistent_fails(self, auth_client):
        assert auth_client.delete(
            "/api/v1/calendar/reminders/99999"
        ).status_code == 404


class TestScheduleReminder:

    def _times(self, offset=2, duration=1):
        start = datetime.now(timezone.utc) + timedelta(hours=offset)
        end   = start + timedelta(hours=duration)
        return {"start_at": start.isoformat(), "end_at": end.isoformat()}

    def test_schedule_creates_event(self, auth_client, reminder_id):
        response = auth_client.post(
            f"/api/v1/calendar/reminders/{reminder_id}/schedule",
            json=self._times(),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["reminder_id"] == reminder_id

    def test_schedule_marks_reminder_scheduled(self, auth_client, reminder_id):
        auth_client.post(
            f"/api/v1/calendar/reminders/{reminder_id}/schedule",
            json=self._times(),
        )
        reminder = next(
            r for r in auth_client.get("/api/v1/calendar/reminders").json()
            if r["id"] == reminder_id
        )
        assert reminder["status"] == "scheduled"

    def test_schedule_twice_fails(self, auth_client, reminder_id):
        auth_client.post(
            f"/api/v1/calendar/reminders/{reminder_id}/schedule",
            json=self._times(),
        )
        response = auth_client.post(
            f"/api/v1/calendar/reminders/{reminder_id}/schedule",
            json=self._times(offset=4),
        )
        assert response.status_code == 409

    def test_schedule_end_before_start_fails(self, auth_client, reminder_id):
        start = datetime.now(timezone.utc) + timedelta(hours=3)
        end   = start - timedelta(hours=1)
        response = auth_client.post(
            f"/api/v1/calendar/reminders/{reminder_id}/schedule",
            json={"start_at": start.isoformat(), "end_at": end.isoformat()},
        )
        assert response.status_code == 422

    def test_schedule_with_dnd_and_reminder(self, auth_client, reminder_id):
        response = auth_client.post(
            f"/api/v1/calendar/reminders/{reminder_id}/schedule",
            json={**self._times(), "enable_dnd": True, "reminder_minutes": 15},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["enable_dnd"] is True
        assert body["reminder_minutes"] == 15

    def test_delete_event_returns_reminder_to_pending(self, auth_client, scheduled_reminder):
        reminder_id, event_id = scheduled_reminder
        auth_client.delete(f"/api/v1/calendar/events/{event_id}")
        reminder = next(
            r for r in auth_client.get("/api/v1/calendar/reminders").json()
            if r["id"] == reminder_id
        )
        assert reminder["status"] == "pending"

    def test_filter_by_status_pending(self, auth_client, scheduled_reminder, urgent_reminder_id):
        _, _ = scheduled_reminder
        response = auth_client.get("/api/v1/calendar/reminders?status=pending")
        statuses = [r["status"] for r in response.json()]
        assert all(s == "pending" for s in statuses)