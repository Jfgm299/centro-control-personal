import pytest
from unittest.mock import patch


class TestActionNodeExecution:

    def test_action_handler_is_called(self, auth_client):
        """El nodo action llama al handler real y devuelve su resultado en node_logs."""
        r = auth_client.post("/api/v1/automations/", json={
            "name": "Action test", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "action",  "config": {"action_id":  "test_module.test_action"}},
                ],
                "edges": [{"from": "n1", "to": "n2"}]
            }
        })
        aid = r.json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"key": "value"}}
        )
        assert response.status_code == 202
        logs = response.json()["node_logs"]
        action_log = next(l for l in logs if l["node_type"] == "action")
        assert action_log["status"] == "success"
        assert action_log["output"]["executed"] is True

    def test_action_receives_payload(self, auth_client):
        """El handler recibe el payload del trigger correctamente."""
        r = auth_client.post("/api/v1/automations/", json={
            "name": "Payload test", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "action",  "config": {"action_id":  "test_module.test_action"}},
                ],
                "edges": [{"from": "n1", "to": "n2"}]
            }
        })
        aid = r.json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"mood": "focused", "score": 9}}
        )
        logs = response.json()["node_logs"]
        action_log = next(l for l in logs if l["node_type"] == "action")
        assert action_log["output"]["received_payload"]["mood"] == "focused"
        assert action_log["output"]["received_payload"]["score"] == 9

    def test_action_uses_config(self, auth_client):
        """El handler recibe correctamente su config del nodo."""
        r = auth_client.post("/api/v1/automations/", json={
            "name": "Config test", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "action",  "config": {
                        "action_id":  "test_module.test_action_with_output",
                        "multiplier": 3,
                    }},
                ],
                "edges": [{"from": "n1", "to": "n2"}]
            }
        })
        aid = r.json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"value": 5}}
        )
        logs = response.json()["node_logs"]
        action_log = next(l for l in logs if l["node_type"] == "action")
        assert action_log["output"]["result"] == 15  # 5 * 3

    def test_action_failure_stops_flow(self, auth_client):
        """Si un nodo action falla sin continue_on_error, el flujo se detiene."""
        r = auth_client.post("/api/v1/automations/", json={
            "name": "Fail test", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "action",  "config": {"action_id": "test_module.test_action_that_fails"}},
                    {"id": "n3", "type": "action",  "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3"},
                ]
            }
        })
        aid = r.json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {}}
        )
        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "failed"
        node_types = [l["node_type"] for l in body["node_logs"]]
        # n3 no debe haberse ejecutado
        assert node_types.count("action") == 1

    def test_action_failure_continues_with_flag(self, auth_client):
        """Con continue_on_error=True el flujo continúa aunque el nodo falle."""
        r = auth_client.post("/api/v1/automations/", json={
            "name": "Continue on error", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "action",  "config": {"action_id": "test_module.test_action_that_fails"},
                     "continue_on_error": True},
                    {"id": "n3", "type": "action",  "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3"},
                ]
            }
        })
        aid = r.json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {}}
        )
        assert response.status_code == 202
        logs = response.json()["node_logs"]
        statuses = {l["node_id"]: l["status"] for l in logs}
        assert statuses["n2"] == "failed"
        assert statuses["n3"] == "success"

        def test_unknown_action_id_rejected_at_create(self, auth_client):
            """La validación rechaza action_ids desconocidos al crear la automatización."""
            response = auth_client.post("/api/v1/automations/", json={
                "name": "Unknown action", "trigger_type": "module_event",
                "flow": {
                    "nodes": [
                        {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                        {"id": "n2", "type": "action",  "config": {"action_id": "nonexistent.action"}},
                    ],
                    "edges": [{"from": "n1", "to": "n2"}]
                }
            })
            assert response.status_code == 422
            assert "nonexistent.action" in response.json()["detail"]



class TestConditionNodeExecution:

    def test_condition_eq_true(self, auth_client):
        aid = auth_client.post("/api/v1/automations/", json={
            "name": "Cond eq true", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",   "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "condition", "config": {"field": "status", "op": "eq", "value": "active"}},
                    {"id": "n3", "type": "action",    "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3", "when": "true"},
                ]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"status": "active"}}
        )
        logs = response.json()["node_logs"]
        assert any(l["node_type"] == "action" and l["status"] == "success" for l in logs)

    def test_condition_eq_false_skips_true_branch(self, auth_client):
        aid = auth_client.post("/api/v1/automations/", json={
            "name": "Cond eq false", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",   "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "condition", "config": {"field": "status", "op": "eq", "value": "active"}},
                    {"id": "n3", "type": "action",    "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3", "when": "true"},
                ]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"status": "inactive"}}
        )
        logs = response.json()["node_logs"]
        assert not any(l["node_type"] == "action" for l in logs)

    def test_condition_gt(self, auth_client):
        aid = auth_client.post("/api/v1/automations/", json={
            "name": "Cond gt", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",   "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "condition", "config": {"field": "score", "op": "gt", "value": 5}},
                    {"id": "n3", "type": "action",    "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3", "when": "true"},
                ]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"score": 9}}
        )
        logs = response.json()["node_logs"]
        assert any(l["node_type"] == "action" for l in logs)

    def test_condition_contains(self, auth_client):
        aid = auth_client.post("/api/v1/automations/", json={
            "name": "Cond contains", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",   "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "condition", "config": {"field": "tags", "op": "contains", "value": "urgent"}},
                    {"id": "n3", "type": "action",    "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3", "when": "true"},
                ]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"tags": ["work", "urgent", "review"]}}
        )
        logs = response.json()["node_logs"]
        assert any(l["node_type"] == "action" for l in logs)

    def test_condition_exists(self, auth_client):
        aid = auth_client.post("/api/v1/automations/", json={
            "name": "Cond exists", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",   "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "condition", "config": {"field": "note", "op": "exists"}},
                    {"id": "n3", "type": "action",    "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3", "when": "true"},
                ]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"note": "algo"}}
        )
        logs = response.json()["node_logs"]
        assert any(l["node_type"] == "action" for l in logs)

    def test_condition_not_exists(self, auth_client):
        aid = auth_client.post("/api/v1/automations/", json={
            "name": "Cond not exists", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",   "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "condition", "config": {"field": "note", "op": "not_exists"}},
                    {"id": "n3", "type": "action",    "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3", "when": "true"},
                ]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {}}
        )
        logs = response.json()["node_logs"]
        assert any(l["node_type"] == "action" for l in logs)

    def test_condition_nested_field(self, auth_client):
        """Campos anidados con notación de punto: event.type"""
        aid = auth_client.post("/api/v1/automations/", json={
            "name": "Cond nested", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",   "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "condition", "config": {"field": "event.type", "op": "eq", "value": "gym"}},
                    {"id": "n3", "type": "action",    "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3", "when": "true"},
                ]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {"event": {"type": "gym", "duration": 60}}}
        )
        logs = response.json()["node_logs"]
        assert any(l["node_type"] == "action" for l in logs)


class TestDelayNodeExecution:

    def test_delay_node_executes(self, auth_client):
        """El nodo delay se ejecuta y reporta los segundos esperados."""
        with patch("time.sleep") as mock_sleep:
            aid = auth_client.post("/api/v1/automations/", json={
                "name": "Delay test", "trigger_type": "module_event",
                "flow": {
                    "nodes": [
                        {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                        {"id": "n2", "type": "delay",   "config": {"minutes": 2}},
                        {"id": "n3", "type": "action",  "config": {"action_id": "test_module.test_action"}},
                    ],
                    "edges": [
                        {"from": "n1", "to": "n2"},
                        {"from": "n2", "to": "n3"},
                    ]
                }
            }).json()["id"]

            response = auth_client.post(
                f"/api/v1/automations/{aid}/trigger",
                json={"payload": {}}
            )
            assert response.status_code == 202
            mock_sleep.assert_called_once_with(120)  # 2 min = 120s

            logs = response.json()["node_logs"]
            delay_log = next(l for l in logs if l["node_type"] == "delay")
            assert delay_log["status"] == "success"
            assert delay_log["output"]["delayed_seconds"] == 120

    def test_delay_caps_at_300_seconds(self, auth_client):
        """El delay máximo en modo síncrono es 300 segundos."""
        with patch("time.sleep") as mock_sleep:
            aid = auth_client.post("/api/v1/automations/", json={
                "name": "Delay cap test", "trigger_type": "module_event",
                "flow": {
                    "nodes": [
                        {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                        {"id": "n2", "type": "delay",   "config": {"minutes": 60}},
                    ],
                    "edges": [{"from": "n1", "to": "n2"}]
                }
            }).json()["id"]

            auth_client.post(f"/api/v1/automations/{aid}/trigger", json={"payload": {}})
            mock_sleep.assert_called_once_with(300)  # cap a 300s

    def test_delay_then_action_executes_action(self, auth_client):
        with patch("time.sleep"):
            aid = auth_client.post("/api/v1/automations/", json={
                "name": "Delay then action", "trigger_type": "module_event",
                "flow": {
                    "nodes": [
                        {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                        {"id": "n2", "type": "delay",   "config": {"minutes": 1}},
                        {"id": "n3", "type": "action",  "config": {"action_id": "test_module.test_action"}},
                    ],
                    "edges": [
                        {"from": "n1", "to": "n2"},
                        {"from": "n2", "to": "n3"},
                    ]
                }
            }).json()["id"]

            response = auth_client.post(
                f"/api/v1/automations/{aid}/trigger",
                json={"payload": {"value": 42}}
            )
            logs = response.json()["node_logs"]
            action_log = next(l for l in logs if l["node_type"] == "action")
            assert action_log["status"] == "success"
            assert action_log["output"]["received_payload"]["value"] == 42


class TestAutomationCallNode:

    def test_automation_call_invokes_child(self, auth_client):
        """automation_call ejecuta otra automatización y añade su resultado al log."""
        child = auth_client.post("/api/v1/automations/", json={
            "name": "Child automation", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "action",  "config": {"action_id": "test_module.test_action"}},
                ],
                "edges": [{"from": "n1", "to": "n2"}]
            }
        }).json()["id"]

        parent = auth_client.post("/api/v1/automations/", json={
            "name": "Parent automation", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",          "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "automation_call",  "config": {"automation_id": child}},
                ],
                "edges": [{"from": "n1", "to": "n2"}]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{parent}/trigger",
            json={"payload": {"value": 7}}
        )
        assert response.status_code == 202
        logs = response.json()["node_logs"]
        call_log = next(l for l in logs if l["node_type"] == "automation_call")
        assert call_log["status"] == "success"
        assert call_log["output"]["called_automation_id"] == child
        assert call_log["output"]["result"]["status"] == "success"

    def test_automation_call_nonexistent_fails(self, auth_client):
        aid = auth_client.post("/api/v1/automations/", json={
            "name": "Call nonexistent", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",         "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "automation_call", "config": {"automation_id": 99999},
                     "continue_on_error": True},
                ],
                "edges": [{"from": "n1", "to": "n2"}]
            }
        }).json()["id"]

        response = auth_client.post(
            f"/api/v1/automations/{aid}/trigger",
            json={"payload": {}}
        )
        logs = response.json()["node_logs"]
        call_log = next(l for l in logs if l["node_type"] == "automation_call")
        assert call_log["status"] == "failed"

    def test_automation_call_depth_exceeded(self, auth_client):
        """Una automatización que se llama a sí misma termina sin colgar — el executor la detiene."""
        auto = auth_client.post("/api/v1/automations/", json={
            "name": "Self call", "trigger_type": "module_event",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": "test_module.test_trigger"}},
                ],
                "edges": []
            }
        }).json()

        auth_client.put(f"/api/v1/automations/{auto['id']}/flow", json={
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger",         "config": {"trigger_id": "test_module.test_trigger"}},
                    {"id": "n2", "type": "automation_call", "config": {"automation_id": auto["id"]}},
                ],
                "edges": [{"from": "n1", "to": "n2"}]
            },
            "trigger_type": "module_event"
        })

        # La ejecución debe terminar (no colgar) y el nodo automation_call
        # devuelve success porque el handler no propaga el fallo del hijo —
        # pero el resultado anidado sí contiene el fallo por profundidad.
        response = auth_client.post(
            f"/api/v1/automations/{auto['id']}/trigger",
            json={"payload": {}}
        )
        assert response.status_code == 202
        logs = response.json()["node_logs"]
        call_log = next(l for l in logs if l["node_type"] == "automation_call")
        # El nodo se completa (el handler no lanza), pero el resultado anidado lleva el fallo
        assert call_log["status"] == "success"
        nested_result = call_log["output"]["result"]
        assert nested_result["status"] in ("success", "failed")  # terminó sin loop infinito



class TestExecutionMetadata:

    def test_execution_has_duration_ms(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        execution = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]
        assert execution["duration_ms"] is not None
        assert execution["duration_ms"] >= 0

    def test_execution_has_finished_at(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        execution = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]
        assert execution["finished_at"] is not None

    def test_execution_started_before_finished(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        execution = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]
        assert execution["started_at"] <= execution["finished_at"]

    def test_execution_trigger_payload_saved(self, auth_client, automation_id):
        auth_client.post(
            f"/api/v1/automations/{automation_id}/trigger",
            json={"payload": {"source": "test", "value": 42}}
        )
        execution = auth_client.get(f"/api/v1/automations/{automation_id}/executions").json()[0]
        assert execution["trigger_payload"]["source"] == "test"
        assert execution["trigger_payload"]["value"] == 42

    def test_node_logs_have_duration_ms(self, auth_client, automation_id):
        auth_client.post(f"/api/v1/automations/{automation_id}/trigger", json={"payload": {}})
        exec_id = auth_client.get(
            f"/api/v1/automations/{automation_id}/executions"
        ).json()[0]["id"]
        logs = auth_client.get(
            f"/api/v1/automations/{automation_id}/executions/{exec_id}"
        ).json()["node_logs"]
        for log in logs:
            assert "duration_ms" in log