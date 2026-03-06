import pytest


class TestAutomationsAuth:

    def test_list_without_token_fails(self, client):
        assert client.get("/api/v1/automations/").status_code == 401

    def test_create_without_token_fails(self, client, automation_data):
        assert client.post("/api/v1/automations/", json=automation_data).status_code == 401

    def test_get_by_id_without_token_fails(self, client, auth_client, automation_id):
        assert client.get(f"/api/v1/automations/{automation_id}").status_code == 401

    def test_delete_without_token_fails(self, client, auth_client, automation_id):
        assert client.delete(f"/api/v1/automations/{automation_id}").status_code == 401


class TestAutomationsOwnership:

    def test_cannot_get_other_users_automation(self, auth_client, other_auth_client, automation_id):
        assert other_auth_client.get(f"/api/v1/automations/{automation_id}").status_code == 404

    def test_cannot_update_other_users_automation(self, auth_client, other_auth_client, automation_id):
        assert other_auth_client.patch(
            f"/api/v1/automations/{automation_id}", json={"name": "Hacked"}
        ).status_code == 404

    def test_cannot_delete_other_users_automation(self, auth_client, other_auth_client, automation_id):
        assert other_auth_client.delete(f"/api/v1/automations/{automation_id}").status_code == 404

    def test_users_see_only_their_automations(self, auth_client, other_auth_client, automation_id):
        other_auth_client.post("/api/v1/automations/", json={
            "name": "Other automation", "trigger_type": "module_event",
            "flow": {"nodes": [{"id": "n1", "type": "trigger", "config": {}}], "edges": []}
        })
        response = auth_client.get("/api/v1/automations/")
        assert len(response.json()) == 1


class TestCreateAutomation:

    def test_create_success(self, auth_client, automation_data):
        response = auth_client.post("/api/v1/automations/", json=automation_data)
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["name"] == automation_data["name"]
        assert body["is_active"] is True
        assert body["run_count"] == 0

    def test_create_minimal(self, auth_client):
        response = auth_client.post("/api/v1/automations/", json={
            "name": "Minimal",
            "trigger_type": "module_event",
            "flow": {"nodes": [{"id": "n1", "type": "trigger", "config": {}}], "edges": []}
        })
        assert response.status_code == 201

    def test_create_duplicate_name_fails(self, auth_client, automation_data, automation_id):
        response = auth_client.post("/api/v1/automations/", json=automation_data)
        assert response.status_code == 409

    def test_create_empty_name_fails(self, auth_client, automation_data):
        automation_data["name"] = ""
        assert auth_client.post("/api/v1/automations/", json=automation_data).status_code == 422

    def test_create_flow_without_trigger_fails(self, auth_client):
        response = auth_client.post("/api/v1/automations/", json={
            "name": "No trigger",
            "trigger_type": "module_event",
            "flow": {
                "nodes": [{"id": "n1", "type": "action", "config": {"action_id": "test"}}],
                "edges": []
            }
        })
        assert response.status_code == 422

    def test_create_with_conditional_flow(self, auth_client, conditional_flow):
        response = auth_client.post("/api/v1/automations/", json={
            "name": "Conditional", "trigger_type": "module_event", "flow": conditional_flow
        })
        assert response.status_code == 201

    def test_create_with_webhook_trigger(self, auth_client, webhook_flow):
        response = auth_client.post("/api/v1/automations/", json={
            "name": "Webhook auto", "trigger_type": "webhook", "flow": webhook_flow
        })
        assert response.status_code == 201

    def test_create_response_fields(self, auth_client, automation_data):
        body = auth_client.post("/api/v1/automations/", json=automation_data).json()
        for field in ["id", "name", "description", "is_active", "flow",
                      "trigger_type", "run_count", "created_at"]:
            assert field in body


class TestGetAutomation:

    def test_get_list_empty(self, auth_client):
        assert auth_client.get("/api/v1/automations/").json() == []

    def test_get_list_returns_created(self, auth_client, automation_id):
        response = auth_client.get("/api/v1/automations/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_by_id_success(self, auth_client, automation_id):
        response = auth_client.get(f"/api/v1/automations/{automation_id}")
        assert response.status_code == 200
        assert response.json()["id"] == automation_id

    def test_get_by_id_not_found(self, auth_client):
        assert auth_client.get("/api/v1/automations/99999").status_code == 404


class TestUpdateAutomation:

    def test_update_name(self, auth_client, automation_id):
        response = auth_client.patch(f"/api/v1/automations/{automation_id}", json={"name": "New Name"})
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_update_description(self, auth_client, automation_id):
        response = auth_client.patch(f"/api/v1/automations/{automation_id}", json={"description": "Nueva desc"})
        assert response.status_code == 200
        assert response.json()["description"] == "Nueva desc"

    def test_deactivate(self, auth_client, automation_id):
        response = auth_client.patch(f"/api/v1/automations/{automation_id}", json={"is_active": False})
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_update_nonexistent_fails(self, auth_client):
        assert auth_client.patch("/api/v1/automations/99999", json={"name": "X"}).status_code == 404

    def test_update_to_duplicate_name_fails(self, auth_client, automation_id, simple_flow):
        auth_client.post("/api/v1/automations/", json={
            "name": "Second", "trigger_type": "module_event", "flow": simple_flow
        })
        assert auth_client.patch(
            f"/api/v1/automations/{automation_id}", json={"name": "Second"}
        ).status_code == 409

    def test_update_flow(self, auth_client, automation_id, conditional_flow):
        response = auth_client.put(f"/api/v1/automations/{automation_id}/flow", json={
            "flow": conditional_flow, "trigger_type": "module_event"
        })
        assert response.status_code == 200
        assert len(response.json()["flow"]["nodes"]) == 4


class TestDeleteAutomation:

    def test_delete_success(self, auth_client, automation_id):
        assert auth_client.delete(f"/api/v1/automations/{automation_id}").status_code == 204

    def test_delete_removes_it(self, auth_client, automation_id):
        auth_client.delete(f"/api/v1/automations/{automation_id}")
        assert auth_client.get(f"/api/v1/automations/{automation_id}").status_code == 404

    def test_delete_nonexistent_fails(self, auth_client):
        assert auth_client.delete("/api/v1/automations/99999").status_code == 404

    def test_delete_twice_fails(self, auth_client, automation_id):
        auth_client.delete(f"/api/v1/automations/{automation_id}")
        assert auth_client.delete(f"/api/v1/automations/{automation_id}").status_code == 404


class TestTriggerAutomation:

    def test_trigger_manual_success(self, auth_client, automation_id):
        response = auth_client.post(
            f"/api/v1/automations/{automation_id}/trigger",
            json={"payload": {"enable_dnd": True, "title": "Gym"}}
        )
        assert response.status_code == 202
        body = response.json()
        assert body["status"] in ("success", "failed")
        assert body["automation_id"] == automation_id

    def test_trigger_creates_execution(self, auth_client, automation_id):
        auth_client.post(
            f"/api/v1/automations/{automation_id}/trigger",
            json={"payload": {}}
        )
        executions = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()
        assert len(executions) == 1

    def test_trigger_nonexistent_fails(self, auth_client):
        assert auth_client.post(
            "/api/v1/automations/99999/trigger", json={"payload": {}}
        ).status_code == 404

    def test_trigger_with_conditional_flow_true_branch(self, auth_client, conditional_flow):
        r = auth_client.post("/api/v1/automations/", json={
            "name": "Cond test", "trigger_type": "module_event", "flow": conditional_flow
        })
        aid = r.json()["id"]
        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"enable_dnd": True}}
        )
        assert response.status_code == 202
        logs = response.json()["node_logs"]
        condition_log = next(l for l in logs if l["node_type"] == "condition")
        assert condition_log["output"]["condition_result"] is True

    def test_trigger_with_conditional_flow_false_branch(self, auth_client, conditional_flow):
        r = auth_client.post("/api/v1/automations/", json={
            "name": "Cond false", "trigger_type": "module_event", "flow": conditional_flow
        })
        aid = r.json()["id"]
        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"enable_dnd": False}}
        )
        assert response.status_code == 202
        logs = response.json()["node_logs"]
        node_types = [l["node_type"] for l in logs]
        assert "stop" in node_types
        assert "action" not in node_types