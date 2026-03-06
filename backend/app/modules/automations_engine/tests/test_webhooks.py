import pytest
from unittest.mock import patch, MagicMock


class TestWebhooksAuth:

    def test_list_without_token_fails(self, client, auth_client, webhook_automation_id):
        assert client.get(
            f"/api/v1/automations/{webhook_automation_id}/webhooks"
        ).status_code == 401

    def test_create_without_token_fails(self, client, auth_client, webhook_automation_id):
        assert client.post(
            f"/api/v1/automations/{webhook_automation_id}/webhooks",
            json={"name": "test"}
        ).status_code == 401


class TestWebhooksOwnership:

    def test_cannot_list_other_users_webhooks(self, auth_client, other_auth_client, webhook_automation_id):
        assert other_auth_client.get(
            f"/api/v1/automations/{webhook_automation_id}/webhooks"
        ).status_code == 404

    def test_cannot_delete_other_users_webhook(self, auth_client, other_auth_client, webhook_token, webhook_automation_id):
        webhook_id = auth_client.get(
            f"/api/v1/automations/{webhook_automation_id}/webhooks"
        ).json()[0]["id"]
        assert other_auth_client.delete(
            f"/api/v1/automations/webhooks/{webhook_id}"
        ).status_code == 404


class TestCreateWebhook:

    def test_create_success(self, auth_client, webhook_automation_id):
        response = auth_client.post(
            f"/api/v1/automations/{webhook_automation_id}/webhooks",
            json={"name": "Mi Shortcut"}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["token"] is not None
        assert len(body["token"]) > 20
        assert body["name"] == "Mi Shortcut"
        assert body["is_active"] is True

    def test_create_generates_unique_tokens(self, auth_client, webhook_automation_id):
        r1 = auth_client.post(
            f"/api/v1/automations/{webhook_automation_id}/webhooks",
            json={"name": "Webhook 1"}
        )
        r2 = auth_client.post(
            f"/api/v1/automations/{webhook_automation_id}/webhooks",
            json={"name": "Webhook 2"}
        )
        assert r1.json()["token"] != r2.json()["token"]

    def test_create_empty_name_fails(self, auth_client, webhook_automation_id):
        assert auth_client.post(
            f"/api/v1/automations/{webhook_automation_id}/webhooks",
            json={"name": ""}
        ).status_code == 422


class TestDeleteWebhook:

    def test_delete_success(self, auth_client, webhook_automation_id):
        webhook_id = auth_client.post(
            f"/api/v1/automations/{webhook_automation_id}/webhooks",
            json={"name": "To delete"}
        ).json()["id"]
        assert auth_client.delete(f"/api/v1/automations/webhooks/{webhook_id}").status_code == 204

    def test_delete_removes_it(self, auth_client, webhook_automation_id):
        webhook_id = auth_client.post(
            f"/api/v1/automations/{webhook_automation_id}/webhooks",
            json={"name": "To delete"}
        ).json()["id"]
        auth_client.delete(f"/api/v1/automations/webhooks/{webhook_id}")
        webhooks = auth_client.get(
            f"/api/v1/automations/{webhook_automation_id}/webhooks"
        ).json()
        assert all(w["id"] != webhook_id for w in webhooks)

    def test_delete_nonexistent_fails(self, auth_client):
        assert auth_client.delete("/api/v1/automations/webhooks/99999").status_code == 404


class TestInboundWebhook:

    def test_inbound_webhook_triggers_automation(self, auth_client, webhook_token):
        with patch("httpx.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code  = 200
            mock_resp.is_success   = True
            mock_resp.text         = "ok"
            mock_req.return_value  = mock_resp

            response = auth_client.post(
                f"/api/v1/webhooks/in/{webhook_token}",
                json={"source": "iphone_shortcuts", "data": {"mood": "focused"}}
            )
            assert response.status_code == 202
            body = response.json()
            assert "execution_id" in body
            assert body["status"] in ("success", "failed")

    def test_inbound_webhook_invalid_token_fails(self, auth_client):
        response = auth_client.post(
            "/api/v1/webhooks/in/invalid_token_xyz",
            json={"source": "test", "data": {}}
        )
        assert response.status_code == 404

    def test_inbound_webhook_calls_outbound(self, auth_client, webhook_token):
        with patch("httpx.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.is_success  = True
            mock_resp.text        = "ok"
            mock_req.return_value = mock_resp

            auth_client.post(
                f"/api/v1/webhooks/in/{webhook_token}",
                json={"source": "test", "data": {"key": "value"}}
            )
            mock_req.assert_called_once()
            call_kwargs = mock_req.call_args
            assert call_kwargs[1]["url"] == "https://example.com/notify"
            assert call_kwargs[1]["method"] == "POST"

    def test_inbound_webhook_payload_passed_to_flow(self, auth_client, webhook_token):
        with patch("httpx.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.is_success  = True
            mock_resp.text        = "ok"
            mock_req.return_value = mock_resp

            auth_client.post(
                f"/api/v1/webhooks/in/{webhook_token}",
                json={"source": "shortcut_gym", "data": {}}
            )
            body_sent = mock_req.call_args[1]["json"]
            assert body_sent["message"] == "shortcut_gym"

    def test_inbound_webhook_outbound_timeout_continue(self, auth_client, webhook_token):
        import httpx as httpx_module
        with patch("httpx.request", side_effect=httpx_module.TimeoutException("timeout")):
            response = auth_client.post(
                f"/api/v1/webhooks/in/{webhook_token}",
                json={"source": "test", "data": {}}
            )
            assert response.status_code == 202

    def test_inbound_webhook_no_auth_required(self, client, webhook_token):
        with patch("httpx.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.is_success  = True
            mock_resp.text        = "ok"
            mock_req.return_value = mock_resp

            response = client.post(
                f"/api/v1/webhooks/in/{webhook_token}",
                json={"source": "external", "data": {}}
            )
            assert response.status_code == 202

    def test_inbound_webhook_creates_execution_log(self, auth_client, webhook_token, webhook_automation_id):
        with patch("httpx.request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.is_success  = True
            mock_resp.text        = "ok"
            mock_req.return_value = mock_resp

            auth_client.post(
                f"/api/v1/webhooks/in/{webhook_token}",
                json={"source": "test", "data": {}}
            )
            executions = auth_client.get(
                f"/api/v1/automations/{webhook_automation_id}/executions"
            ).json()
            assert len(executions) == 1