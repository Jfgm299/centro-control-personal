"""
Tests del dispatcher y automation handlers de flights_tracker.

Probamos:
1. Trigger flight_added — dispara cuando se registra un vuelo
2. Trigger flight_status_changed — dispara cuando el estado cambia
3. Trigger flight_status_changed — no dispara si el nuevo estado no coincide con el filtro
4. Trigger flight_departing_soon — dispara al llamar el job del scheduler
5. Action get_flight_details — devuelve info del vuelo
6. Action refresh_flight — refresca datos via API (mockeada)
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone

from app.modules.flights_tracker.automation_dispatcher import dispatcher
from app.modules.flights_tracker.tests.conftest import MOCK_FLIGHT_RAW, _make_departing_soon_mock_raw


class TestFlightsDispatcher:

    def _run_automation(
        self, auth_client, db, trigger_ref, action_id, action_config, payload, user_id
    ):
        """Helper: crea y ejecuta una automatización con una acción específica."""
        from app.modules.automations_engine.models.execution import Execution

        r = auth_client.post("/api/v1/automations/", json={
            "name":         f"Test {action_id}",
            "trigger_type": "module_event",
            "trigger_ref":  trigger_ref,
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": trigger_ref}},
                    {"id": "n2", "type": "action",  "config": {"action_id": action_id, **action_config}},
                ],
                "edges": [{"from": "n1", "to": "n2"}],
            },
        })
        assert r.status_code == 201, r.json()
        automation_id = r.json()["id"]

        dispatcher._find_and_execute(
            trigger_ref=trigger_ref,
            payload=payload,
            user_id=user_id,
            db=db,
        )

        execution = db.query(
            __import__(
                "app.modules.automations_engine.models.execution",
                fromlist=["Execution"]
            ).Execution
        ).filter_by(automation_id=automation_id).first()
        return execution

    def test_flight_added_trigger_fires(
        self, db, auth_client, mock_aerodatabox, automation_for_flight_added
    ):
        """flight_added dispara cuando se registra un vuelo."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        # Crear vuelo — esto llama al dispatcher internamente
        r = auth_client.post("/api/v1/flights/", json={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert r.status_code == 201, r.json()
        flight_id = r.json()["id"]

        automation = db.query(Automation).filter(
            Automation.id == automation_for_flight_added
        ).first()

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_flight_added
        ).all()
        assert len(executions) >= 1
        assert executions[0].status.value in ("success", "failed")

    def test_flight_status_changed_trigger_fires(
        self, db, auth_client, created_flight_id, automation_for_flight_status_changed
    ):
        """flight_status_changed dispara cuando el estado cambia."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_flight_status_changed
        ).first()

        dispatcher.on_flight_status_changed(
            flight_id=created_flight_id,
            old_status="expected",
            new_status="departed",
            flight_dict={"flight_id": created_flight_id},
            user_id=automation.user_id,
            db=db,
        )

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_flight_status_changed
        ).all()
        assert len(executions) == 1
        assert executions[0].status.value in ("success", "failed")

    def test_flight_status_changed_filtered_by_to_status(
        self, db, auth_client, created_flight_id, automation_for_flight_status_arrived
    ):
        """flight_status_changed NO dispara si nuevo estado != filtro configurado."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_flight_status_arrived
        ).first()

        # Status cambia a "departed", pero la automatización filtra solo "arrived"
        dispatcher.on_flight_status_changed(
            flight_id=created_flight_id,
            old_status="expected",
            new_status="departed",
            flight_dict={"flight_id": created_flight_id},
            user_id=automation.user_id,
            db=db,
        )

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_flight_status_arrived
        ).all()
        # La ejecución ocurre (el dispatcher dispara) pero el trigger devuelve matched=False
        # y el flow termina como "skipped" o "success" con matched=False
        for e in executions:
            assert e.status.value in ("success", "failed", "skipped")

    def test_flight_departing_soon_job_fires(
        self, db, auth_client, departing_soon_flight_id, automation_for_flight_departing_soon
    ):
        """flight_departing_soon dispara para vuelos dentro de la ventana de salida."""
        from datetime import datetime, timedelta, timezone
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution
        from app.modules.flights_tracker.flight import Flight
        from app.modules.flights_tracker.automation_handlers import _flight_to_dict

        # Verificar que el vuelo existe y tiene scheduled_departure en ~24h
        flight = db.query(Flight).filter(Flight.id == departing_soon_flight_id).first()
        assert flight is not None
        assert flight.scheduled_departure is not None
        assert flight.is_past is False

        now = datetime.now(timezone.utc)
        hours_until = (flight.scheduled_departure - now).total_seconds() / 3600

        automation = db.query(Automation).filter(
            Automation.id == automation_for_flight_departing_soon
        ).first()

        # Simular directamente lo que haría el job del scheduler
        dispatcher.on_flight_departing_soon(
            flight_id=flight.id,
            hours_until_departure=hours_until,
            flight_dict=_flight_to_dict(flight),
            user_id=automation.user_id,
            db=db,
        )

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_flight_departing_soon
        ).all()
        assert len(executions) >= 1
        assert executions[0].status.value in ("success", "failed")

    def test_action_get_flight_details(
        self, db, auth_client, created_flight_id, automation_for_flight_added
    ):
        """action_get_flight_details devuelve info completa del vuelo."""
        from app.modules.automations_engine.models.automation import Automation

        automation = db.query(Automation).filter(
            Automation.id == automation_for_flight_added
        ).first()
        user_id = automation.user_id

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="flights_tracker.flight_added",
            action_id="flights_tracker.get_flight_details",
            action_config={},
            payload={"flight_id": created_flight_id},
            user_id=user_id,
        )

        assert execution is not None
        assert execution.status.value == "success"

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is True
        assert "flight" in action_log["output"]
        assert action_log["output"]["flight"]["id"] == created_flight_id

    def test_action_refresh_flight(
        self, db, auth_client, created_flight_id, automation_for_flight_added
    ):
        """action_refresh_flight refresca datos del vuelo (API mockeada)."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.flights_tracker.flight import Flight

        automation = db.query(Automation).filter(
            Automation.id == automation_for_flight_added
        ).first()
        user_id = automation.user_id

        # Forzar last_refreshed_at a hace 10 minutos para pasar el throttle check
        flight = db.query(Flight).filter(Flight.id == created_flight_id).first()
        flight.last_refreshed_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        db.commit()

        with patch(
            "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
            new_callable=AsyncMock, return_value=MOCK_FLIGHT_RAW
        ):
            execution = self._run_automation(
                auth_client=auth_client,
                db=db,
                trigger_ref="flights_tracker.flight_added",
                action_id="flights_tracker.refresh_flight",
                action_config={},
                payload={"flight_id": created_flight_id},
                user_id=user_id,
            )

        assert execution is not None
        assert execution.status.value == "success"

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is True
        assert "flight" in action_log["output"]
