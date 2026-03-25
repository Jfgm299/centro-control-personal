import pytest
from app.modules.automations_engine.core.registry import registry


@pytest.fixture(autouse=True, scope="session")
def register_mock_triggers():
    registry.register_trigger(
        module_id="test_module",
        trigger_id="test_trigger",
        label="Test trigger",
        config_schema={},
        handler="app.modules.automations_engine.core.node_handlers.trigger_handler.handle",
    )
    registry.register_trigger(
        module_id="webhook",
        trigger_id="inbound",
        label="Webhook entrante",
        config_schema={},
        handler="app.modules.automations_engine.core.node_handlers.trigger_handler.handle",
    )
    registry.register_action(
        module_id="test_module",
        action_id="test_action",
        label="Test action",
        config_schema={},
        handler="app.modules.automations_engine.tests.handlers_for_testing.handle_test_action",
    )
    registry.register_action(
        module_id="test_module",
        action_id="test_action_with_output",
        label="Test action with output",
        config_schema={},
        handler="app.modules.automations_engine.tests.handlers_for_testing.handle_test_action_with_output",
    )
    registry.register_action(
        module_id="test_module",
        action_id="test_action_that_fails",
        label="Test action that fails",
        config_schema={},
        handler="app.modules.automations_engine.tests.handlers_for_testing.handle_test_action_that_fails",
    )
    yield


# ── Flujos ────────────────────────────────────────────────────────────────────

@pytest.fixture
def simple_flow():
    return {
        "nodes": [
            {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
            {"id": "n2", "type": "action",  "config": {"action_id":  "test_module.test_action"}},
        ],
        "edges": [{"from": "n1", "to": "n2"}]
    }


@pytest.fixture
def conditional_flow():
    return {
        "nodes": [
            {"id": "n1", "type": "trigger",   "config": {"trigger_id": "test_module.test_trigger"}},
            {"id": "n2", "type": "condition", "config": {"field": "enable_dnd", "op": "eq", "value": True}},
            {"id": "n3", "type": "action",    "config": {"action_id": "test_module.test_action"}},
            {"id": "n4", "type": "stop",      "config": {"reason": "dnd not enabled"}},
        ],
        "edges": [
            {"from": "n1", "to": "n2"},
            {"from": "n2", "to": "n3", "when": "true"},
            {"from": "n2", "to": "n4", "when": "false"},
        ]
    }


@pytest.fixture
def webhook_flow():
    return {
        "nodes": [
            {"id": "n1", "type": "trigger",          "config": {"trigger_id": "webhook.inbound"}},
            {"id": "n2", "type": "outbound_webhook",  "config": {
                "url":             "https://example.com/notify",
                "method":          "POST",
                "body_template":   {"message": "{{ source }}"},
                "timeout_seconds": 5,
            }},
        ],
        "edges": [{"from": "n1", "to": "n2"}]
    }


@pytest.fixture
def automation_data(simple_flow):
    return {
        "name":         "Test Automation",
        "description":  "Automatización de prueba",
        "is_active":    True,
        "trigger_type": "module_event",
        "trigger_ref":  "test_module.test_trigger",
        "flow":         simple_flow,
    }


@pytest.fixture
def automation_id(auth_client, automation_data):
    response = auth_client.post("/api/v1/automations/", json=automation_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def webhook_automation_id(auth_client, webhook_flow):
    response = auth_client.post("/api/v1/automations/", json={
        "name":         "Webhook Automation",
        "trigger_type": "webhook",
        "flow":         webhook_flow,
    })
    assert response.status_code == 201, response.json()
    return response.json()["id"]


@pytest.fixture
def webhook_token(auth_client, webhook_automation_id):
    response = auth_client.post(
        f"/api/v1/automations/{webhook_automation_id}/webhooks",
        json={"name": "Test Webhook"}
    )
    assert response.status_code == 201, response.json()
    return response.json()["token"]


@pytest.fixture
def api_key_data():
    return {"name": "Test API Key", "scopes": ["trigger", "read"]}


@pytest.fixture
def api_key_id_and_token(auth_client, api_key_data):
    response = auth_client.post("/api/v1/automations/api-keys/", json=api_key_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"], response.json()["token"]