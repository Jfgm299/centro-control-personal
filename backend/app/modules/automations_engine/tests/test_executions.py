import pytest


class TestExecutionsAuth:

    def test_list_without_token_fails(self, client, auth_client, automation_id):
        assert client.get(f"/api/v1/automations/{automation_id}/executions").status_code == 401

    def test_get_by_id_without_token_fails(self, client, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        exec_id = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]["id"]
        assert client.get(f"/api/v1/automations/{automation_id}/executions/{exec_id}").status_code == 401


class TestExecutionsOwnership:

    def test_cannot_see_other_users_executions(self, auth_client, other_auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        response = other_auth_client.get(f"/api/v1/automations/{automation_id}/executions")
        assert response.status_code == 404

    def test_cannot_see_other_users_execution_detail(self, auth_client, other_auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        exec_id = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]["id"]
        assert other_auth_client.get(
            f"/api/v1/automations/{automation_id}/executions/{exec_id}"
        ).status_code == 404


class TestGetExecutions:

    def test_list_empty(self, auth_client, automation_id):
        assert auth_client.get(f"/api/v1/automations/{automation_id}/executions").json() == []

    def test_list_after_trigger(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        executions = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()
        assert len(executions) == 1

    def test_multiple_triggers_create_multiple_executions(self, auth_client, automation_id):
        for _ in range(3):
            auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        executions = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()
        assert len(executions) == 3

    def test_execution_response_fields(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        execution = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]
        for field in ["id", "automation_id", "status", "started_at", "node_logs"]:
            assert field in execution

    def test_execution_status_is_success_or_failed(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        execution = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]
        assert execution["status"] in ("success", "failed")

    def test_get_execution_detail(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        exec_id = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]["id"]
        response = auth_client.get(f"/api/v1/automations/{automation_id}/executions/{exec_id}")
        assert response.status_code == 200
        assert response.json()["id"] == exec_id

    def test_execution_contains_node_logs(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        exec_id = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]["id"]
        execution = auth_client.get(
            f"/api/v1/automations/{automation_id}/executions/{exec_id}"
        ).json()
        assert isinstance(execution["node_logs"], list)
        assert len(execution["node_logs"]) > 0

    def test_node_logs_have_required_fields(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        exec_id = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]["id"]
        logs = auth_client.get(
            f"/api/v1/automations/{automation_id}/executions/{exec_id}"
        ).json()["node_logs"]
        for log in logs:
            assert "node_id"   in log
            assert "node_type" in log
            assert "status"    in log

    def test_get_execution_not_found(self, auth_client, automation_id):
        assert auth_client.get(
            f"/api/v1/automations/{automation_id}/executions/99999"
        ).status_code == 404