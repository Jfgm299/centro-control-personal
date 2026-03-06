import pytest
from datetime import datetime, timezone, timedelta


def _range(offset=2, duration=1):
    start = datetime.now(timezone.utc) + timedelta(hours=offset)
    end   = start + timedelta(hours=duration)
    return {"start_at": start.isoformat(), "end_at": end.isoformat()}


class TestEventsAuth:

    def test_list_without_token_fails(self, client):
        start = datetime.now(timezone.utc).isoformat()
        end   = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        assert client.get(
            f"/api/v1/calendar/events?start={start}&end={end}"
        ).status_code == 401

    def test_create_without_token_fails(self, client):
        assert client.post("/api/v1/calendar/events", json={}).status_code == 401


class TestEventsOwnership:

    def test_cannot_update_other_users_event(self, auth_client, other_auth_client, event_id):
        assert other_auth_client.patch(
            f"/api/v1/calendar/events/{event_id}", json={"title": "Hack"}
        ).status_code == 404

    def test_cannot_delete_other_users_event(self, auth_client, other_auth_client, event_id):
        assert other_auth_client.delete(
            f"/api/v1/calendar/events/{event_id}"
        ).status_code == 404

    def test_cannot_complete_other_users_event(self, auth_client, other_auth_client, event_id):
        assert other_auth_client.patch(
            f"/api/v1/calendar/events/{event_id}/complete"
        ).status_code == 404


class TestCreateEvent:

    def test_create_success(self, auth_client, event_data):
        response = auth_client.post("/api/v1/calendar/events", json=event_data)
        assert response.status_code == 201
        body = response.json()
        assert body["title"]       == event_data["title"]
        assert body["is_cancelled"] is False
        assert body["enable_dnd"]   is False

    def test_create_with_dnd(self, auth_client):
        response = auth_client.post("/api/v1/calendar/events", json={
            "title": "Examen", "enable_dnd": True, **_range(),
        })
        assert response.status_code == 201
        assert response.json()["enable_dnd"] is True

    def test_create_with_reminder_minutes(self, auth_client):
        response = auth_client.post("/api/v1/calendar/events", json={
            "title": "Con recordatorio", "reminder_minutes": 30, **_range(),
        })
        assert response.status_code == 201
        assert response.json()["reminder_minutes"] == 30

    def test_create_end_before_start_fails(self, auth_client):
        start = datetime.now(timezone.utc) + timedelta(hours=2)
        end   = start - timedelta(hours=1)
        assert auth_client.post("/api/v1/calendar/events", json={
            "title": "Mal rango",
            "start_at": start.isoformat(),
            "end_at":   end.isoformat(),
        }).status_code == 422

    def test_create_with_category(self, auth_client, category_id):
        response = auth_client.post("/api/v1/calendar/events", json={
            "title": "Con categoria", "category_id": category_id, **_range(),
        })
        assert response.status_code == 201
        body = response.json()
        assert body["category_id"] == category_id
        assert body["category"]["id"] == category_id

    def test_create_with_color_override(self, auth_client):
        response = auth_client.post("/api/v1/calendar/events", json={
            "title": "Con color", "color_override": "#FF0000", **_range(),
        })
        assert response.status_code == 201
        assert response.json()["color_override"] == "#FF0000"

    def test_create_invalid_reminder_minutes_fails(self, auth_client):
        assert auth_client.post("/api/v1/calendar/events", json={
            "title": "Test", "reminder_minutes": 0, **_range(),
        }).status_code == 422


class TestGetEvent:

    def test_get_by_id(self, auth_client, event_id):
        response = auth_client.get(f"/api/v1/calendar/events/{event_id}")
        assert response.status_code == 200
        assert response.json()["id"] == event_id

    def test_get_nonexistent_fails(self, auth_client):
        assert auth_client.get("/api/v1/calendar/events/99999").status_code == 404

    def test_get_range(self, auth_client, event_id):
        start = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        end   = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        response = auth_client.get("/api/v1/calendar/events", params={"start": start, "end": end})
        assert response.status_code == 200
        ids = [e["id"] for e in response.json() if e["id"] is not None]
        assert event_id in ids

    def test_get_today(self, auth_client, event_id):
        response = auth_client.get("/api/v1/calendar/events/today")
        assert response.status_code == 200
        ids = [e["id"] for e in response.json() if e["id"] is not None]
        assert event_id in ids

    def test_range_end_before_start_fails(self, auth_client):
        start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        end   = datetime.now(timezone.utc).isoformat()
        assert auth_client.get(
            "/api/v1/calendar/events", params={"start": start, "end": end}
        ).status_code == 422


class TestUpdateEvent:

    def test_update_title(self, auth_client, event_id):
        response = auth_client.patch(
            f"/api/v1/calendar/events/{event_id}", json={"title": "Nuevo titulo"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Nuevo titulo"

    def test_update_enable_dnd(self, auth_client, event_id):
        response = auth_client.patch(
            f"/api/v1/calendar/events/{event_id}", json={"enable_dnd": True}
        )
        assert response.status_code == 200
        assert response.json()["enable_dnd"] is True

    def test_update_reminder_minutes(self, auth_client, event_id):
        response = auth_client.patch(
            f"/api/v1/calendar/events/{event_id}", json={"reminder_minutes": 15}
        )
        assert response.status_code == 200
        assert response.json()["reminder_minutes"] == 15

    def test_update_nonexistent_fails(self, auth_client):
        assert auth_client.patch(
            "/api/v1/calendar/events/99999", json={"title": "X"}
        ).status_code == 404

    def test_update_end_before_start_fails(self, auth_client, event_id):
        event = auth_client.get(f"/api/v1/calendar/events/{event_id}").json()
        bad_end = (datetime.fromisoformat(event["start_at"]) - timedelta(hours=1)).isoformat()
        assert auth_client.patch(
            f"/api/v1/calendar/events/{event_id}",
            json={"end_at": bad_end},
        ).status_code == 422


class TestCompleteEvent:

    def test_complete_event(self, auth_client, event_id):
        response = auth_client.patch(f"/api/v1/calendar/events/{event_id}/complete")
        assert response.status_code == 200
        assert response.json()["is_cancelled"] is True

    def test_complete_marks_reminder_done(self, auth_client, scheduled_reminder):
        reminder_id, event_id = scheduled_reminder
        auth_client.patch(f"/api/v1/calendar/events/{event_id}/complete")
        reminder = next(
            r for r in auth_client.get("/api/v1/calendar/reminders").json()
            if r["id"] == reminder_id
        )
        assert reminder["status"] == "done"

    def test_complete_nonexistent_fails(self, auth_client):
        assert auth_client.patch(
            "/api/v1/calendar/events/99999/complete"
        ).status_code == 404


class TestDeleteEvent:

    def test_delete_success(self, auth_client, event_id):
        assert auth_client.delete(f"/api/v1/calendar/events/{event_id}").status_code == 204

    def test_delete_nonexistent_fails(self, auth_client):
        assert auth_client.delete("/api/v1/calendar/events/99999").status_code == 404

    def test_delete_removes_from_range(self, auth_client, event_id):
        auth_client.delete(f"/api/v1/calendar/events/{event_id}")
        start = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        end   = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        ids = [
            e["id"] for e in
            auth_client.get("/api/v1/calendar/events", params={"start": start, "end": end}).json()
            if e["id"] is not None
        ]
        assert event_id not in ids