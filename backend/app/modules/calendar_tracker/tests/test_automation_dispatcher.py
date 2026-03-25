"""
Tests del dispatcher y scheduler de automatizaciones de calendar_tracker.

Probamos:
1. El dispatcher encuentra automatizaciones suscritas y las ejecuta
2. Las funciones de job detectan eventos/recordatorios en la ventana correcta
3. Los flujos reales se ejecutan con datos reales de calendar_tracker
"""
import pytest
from datetime import datetime, timezone, timedelta, date
from app.modules.calendar_tracker.automation_dispatcher import dispatcher
from app.modules.calendar_tracker.services.scheduler_service import (
    job_check_event_starts,
    job_check_event_ends,
    job_check_reminders_due,
    job_check_overdue_reminders,
    job_check_free_windows,
)


class TestDispatcherEventStart:

    def test_dispatcher_finds_and_executes_automation(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """El dispatcher ejecuta la automatización suscrita a event_start."""
        from app.modules.automations_engine.models.automation import Automation
        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        dispatcher.on_event_start(
            event_id=event_id,
            user_id=automation.user_id,
            db=db,
        )

        # Verificar que se creó una ejecución
        from app.modules.automations_engine.models.execution import Execution
        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_event_start
        ).all()
        assert len(executions) == 1
        assert executions[0].status.value in ("success", "failed")

    def test_dispatcher_execution_has_event_payload(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """El payload del evento llega correctamente a la ejecución."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        dispatcher.on_event_start(event_id=event_id, user_id=automation.user_id, db=db)

        execution = db.query(Execution).filter(
            Execution.automation_id == automation_for_event_start
        ).first()
        assert execution.trigger_payload["event_id"] == event_id

    def test_dispatcher_inactive_automation_not_executed(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """Una automatización inactiva no se ejecuta."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()
        user_id = automation.user_id

        # Desactivar
        auth_client.patch(
            f"/api/v1/automations/{automation_for_event_start}",
            json={"is_active": False}
        )
        db.refresh(automation)

        dispatcher.on_event_start(event_id=event_id, user_id=user_id, db=db)

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_event_start
        ).all()
        assert len(executions) == 0

    def test_dispatcher_no_automations_no_error(self, db, auth_client, event_id):
        """Si no hay automatizaciones suscritas, no explota."""
        from app.modules.automations_engine.models.execution import Execution

        dispatcher.on_event_start(event_id=event_id, user_id=99999, db=db)

        executions = db.query(Execution).all()
        assert len(executions) == 0

    def test_dispatcher_multiple_automations_all_executed(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """Si hay varias automatizaciones suscritas, se ejecutan todas."""
        # Crear segunda automatización suscrita al mismo trigger
        r = auth_client.post("/api/v1/automations/", json={
            "name":         "Auto event start 2",
            "trigger_type": "module_event",
            "trigger_ref":  "calendar_tracker.event_start",
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": "calendar_tracker.event_start"}},
                    {"id": "n2", "type": "action",  "config": {"action_id": "calendar_tracker.get_todays_schedule"}},
                ],
                "edges": [{"from": "n1", "to": "n2"}]
            }
        })
        second_id = r.json()["id"]

        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        dispatcher.on_event_start(event_id=event_id, user_id=automation.user_id, db=db)

        executions = db.query(Execution).all()
        automation_ids = {e.automation_id for e in executions}
        assert automation_for_event_start in automation_ids
        assert second_id in automation_ids


class TestDispatcherEventEnd:

    def test_dispatcher_event_end_executes(
        self, db, auth_client, event_id, automation_for_event_end
    ):
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_end
        ).first()

        dispatcher.on_event_end(event_id=event_id, user_id=automation.user_id, db=db)

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_event_end
        ).all()
        assert len(executions) == 1


class TestDispatcherReminderDue:

    def test_dispatcher_reminder_due_executes(
        self, db, auth_client, reminder_due_today_id, automation_for_reminder_due
    ):
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_reminder_due
        ).first()

        dispatcher.on_reminder_due(
            reminder_id=reminder_due_today_id,
            user_id=automation.user_id,
            db=db,
        )

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_reminder_due
        ).all()
        assert len(executions) == 1

    def test_dispatcher_reminder_payload_correct(
        self, db, auth_client, reminder_due_today_id, automation_for_reminder_due
    ):
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_reminder_due
        ).first()

        dispatcher.on_reminder_due(
            reminder_id=reminder_due_today_id,
            user_id=automation.user_id,
            db=db,
        )

        execution = db.query(Execution).filter(
            Execution.automation_id == automation_for_reminder_due
        ).first()
        assert execution.trigger_payload["reminder_id"] == reminder_due_today_id


class TestDispatcherOverdue:

    def test_dispatcher_overdue_executes(
        self, db, auth_client, overdue_reminder_id, automation_for_overdue
    ):
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_overdue
        ).first()

        dispatcher.on_overdue_reminders_exist(user_id=automation.user_id, db=db)

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_overdue
        ).all()
        assert len(executions) == 1

    def test_dispatcher_overdue_execution_success(
        self, db, auth_client, overdue_reminder_id, automation_for_overdue
    ):
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_overdue
        ).first()

        dispatcher.on_overdue_reminders_exist(user_id=automation.user_id, db=db)

        execution = db.query(Execution).filter(
            Execution.automation_id == automation_for_overdue
        ).first()
        assert execution.status.value == "success"


class TestSchedulerJobs:

    def test_job_event_starts_detects_event_in_window(
        self, db, auth_client, event_starting_now, automation_for_event_start
    ):
        """job_check_event_starts detecta el evento y ejecuta la automatización."""
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        # Parchamos SessionLocal para que use la misma DB de test
        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_event_starts()

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_event_start
        ).all()
        assert len(executions) >= 1

    def test_job_event_starts_ignores_future_events(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """job_check_event_starts ignora eventos que empiezan en el futuro lejano."""
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_event_starts()

        # event_id empieza en 2 horas — no debe dispararse
        executions = db.query(Execution).all()
        assert len(executions) == 0

    def test_job_event_ends_detects_event_in_window(
        self, db, auth_client, event_ending_now, automation_for_event_end
    ):
        """job_check_event_ends detecta el evento que termina y ejecuta la automatización."""
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_event_ends()

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_event_end
        ).all()
        assert len(executions) >= 1

    def test_job_reminders_due_detects_today(
        self, db, auth_client, reminder_due_today_id, automation_for_reminder_due
    ):
        """job_check_reminders_due detecta recordatorios que vencen hoy."""
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_reminders_due()

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_reminder_due
        ).all()
        assert len(executions) >= 1

    def test_job_reminders_due_ignores_future(
        self, db, auth_client, reminder_id, automation_for_reminder_due
    ):
        """job_check_reminders_due ignora recordatorios sin due_date o con fecha futura."""
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_reminders_due()

        executions = db.query(Execution).all()
        assert len(executions) == 0

    def test_job_overdue_detects_past_reminders(
        self, db, auth_client, overdue_reminder_id, automation_for_overdue
    ):
        """job_check_overdue_reminders detecta recordatorios vencidos del pasado."""
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_overdue_reminders()

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_overdue
        ).all()
        assert len(executions) >= 1

    def test_job_overdue_ignores_users_without_overdue(
        self, db, auth_client, reminder_id, automation_for_overdue
    ):
        """job_check_overdue_reminders no dispara si no hay recordatorios vencidos."""
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_overdue_reminders()

        executions = db.query(Execution).all()
        assert len(executions) == 0

    
    def test_job_free_windows_detects_no_events(
        self, db, auth_client, automation_for_free_window
        ):
        """job_check_free_windows dispara cuando el usuario no tiene eventos próximos."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        automation = db.query(Automation).filter(
            Automation.id == automation_for_free_window
        ).first()

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_free_windows()

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_free_window
        ).all()
        assert len(executions) >= 1
        assert executions[0].status.value == "success"

    def test_job_free_windows_no_dispatch_when_events_exist(
        self, db, auth_client, event_starting_now, automation_for_free_window
    ):
        """job_check_free_windows no dispara si hay eventos en la ventana próxima."""
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_free_windows()

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_free_window
        ).all()
        assert len(executions) == 0


class TestFullFlowIntegration:

    def test_event_start_trigger_runs_full_flow(
        self, db, auth_client, event_starting_now, automation_for_event_start
    ):
        """
        Test de integración completo:
        evento empieza → scheduler detecta → dispatcher ejecuta → flujo completo.
        """
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_event_starts()

        execution = db.query(Execution).filter(
            Execution.automation_id == automation_for_event_start
        ).first()

        assert execution is not None
        assert execution.status.value == "success"
        assert execution.node_logs is not None
        assert len(execution.node_logs) == 2  # trigger + action

        trigger_log = next(l for l in execution.node_logs if l["node_type"] == "trigger")
        action_log  = next(l for l in execution.node_logs if l["node_type"] == "action")

        assert trigger_log["status"] == "success"
        assert action_log["status"]  == "success"
        assert "events" in action_log["output"]  # get_todays_schedule devuelve events

    def test_overdue_reminder_trigger_runs_full_flow(
        self, db, auth_client, overdue_reminder_id, automation_for_overdue
    ):
        """
        Test de integración completo:
        recordatorio vencido → scheduler detecta → dispatcher ejecuta → resumen generado.
        """
        from app.modules.automations_engine.models.execution import Execution
        from unittest.mock import patch

        with patch(
            "app.modules.calendar_tracker.services.scheduler_service._get_db",
            return_value=db
        ):
            job_check_overdue_reminders()

        execution = db.query(Execution).filter(
            Execution.automation_id == automation_for_overdue
        ).first()

        assert execution is not None
        assert execution.status.value == "success"

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["count"] >= 1
        assert "summary" in action_log["output"]




class TestCalendarActions:
    """
    Prueba que cada acción de calendar_tracker produce efectos reales en la DB.
    Crea una automatización con la acción como nodo y verifica el resultado.
    """

    def _run_automation(self, auth_client, db, trigger_ref, action_id, action_config, payload, user_id):
        """Helper: crea y ejecuta una automatización con una acción específica."""
        from app.modules.automations_engine.models.automation import Automation
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
                "edges": [{"from": "n1", "to": "n2"}]
            }
        })
        assert r.status_code == 201, r.json()
        automation_id = r.json()["id"]

        automation = db.query(Automation).filter(Automation.id == automation_id).first()
        dispatcher._find_and_execute(
            trigger_ref=trigger_ref,
            payload=payload,
            user_id=user_id,
            db=db,
        )

        execution = db.query(Execution).filter(
            Execution.automation_id == automation_id
        ).first()
        return execution

    def test_action_create_event_creates_real_event(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """create_event crea un evento real en la DB."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.calendar_tracker.models.event import Event

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()
        user_id = automation.user_id

        events_before = db.query(Event).filter(Event.user_id == user_id).count()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.create_event",
            action_config={"title": "Evento creado por automatización", "duration_minutes": 45},
            payload={"event_id": event_id},
            user_id=user_id,
        )

        assert execution.status.value == "success"
        events_after = db.query(Event).filter(Event.user_id == user_id).count()
        assert events_after == events_before + 1

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["created"] is True
        assert action_log["output"]["event"]["title"] == "Evento creado por automatización"

    def test_action_create_event_respects_duration(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """create_event crea el evento con la duración correcta."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.calendar_tracker.models.event import Event

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.create_event",
            action_config={"title": "Evento 90min", "duration_minutes": 90},
            payload={"event_id": event_id},
            user_id=automation.user_id,
        )

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        event_data = action_log["output"]["event"]
        start = datetime.fromisoformat(event_data["start_at"])
        end   = datetime.fromisoformat(event_data["end_at"])
        duration_minutes = (end - start).seconds // 60
        assert duration_minutes == 90

    def test_action_create_reminder_creates_real_reminder(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """create_reminder crea un recordatorio real en la DB."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.calendar_tracker.models.reminder import Reminder
        from app.modules.calendar_tracker.enums import ReminderStatus

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()
        user_id = automation.user_id

        reminders_before = db.query(Reminder).filter(Reminder.user_id == user_id).count()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.create_reminder",
            action_config={"title": "Recordatorio automático", "priority": "high", "due_in_days": 3},
            payload={"event_id": event_id},
            user_id=user_id,
        )

        assert execution.status.value == "success"
        reminders_after = db.query(Reminder).filter(Reminder.user_id == user_id).count()
        assert reminders_after == reminders_before + 1

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["created"] is True
        assert action_log["output"]["reminder"]["title"] == "Recordatorio automático"
        assert action_log["output"]["reminder"]["status"] == "pending"

    def test_action_create_reminder_sets_due_date(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """create_reminder calcula la due_date correctamente según due_in_days."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.calendar_tracker.models.reminder import Reminder
        from datetime import date

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.create_reminder",
            action_config={"title": "Vence en 7 días", "due_in_days": 7},
            payload={"event_id": event_id},
            user_id=automation.user_id,
        )

        action_log  = next(l for l in execution.node_logs if l["node_type"] == "action")
        reminder_id = action_log["output"]["reminder"]["id"]
        reminder    = db.query(Reminder).filter(Reminder.id == reminder_id).first()

        expected_due = date.today() + timedelta(days=7)
        assert reminder.due_date == expected_due

    def test_action_mark_reminder_done_changes_status(
        self, db, auth_client, reminder_id, automation_for_event_start
    ):
        """mark_reminder_done cambia el status del recordatorio a DONE en la DB."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.calendar_tracker.models.reminder import Reminder
        from app.modules.calendar_tracker.enums import ReminderStatus

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        assert reminder.status == ReminderStatus.PENDING

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.mark_reminder_done",
            action_config={"reminder_id": reminder_id},
            payload={"event_id": reminder_id},
            user_id=automation.user_id,
        )

        assert execution.status.value == "success"
        db.refresh(reminder)
        assert reminder.status == ReminderStatus.DONE

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is True

    def test_action_mark_reminder_done_nonexistent_returns_false(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """mark_reminder_done con reminder inexistente devuelve done=False sin explotar."""
        from app.modules.automations_engine.models.automation import Automation

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.mark_reminder_done",
            action_config={"reminder_id": 99999},
            payload={"event_id": event_id},
            user_id=automation.user_id,
        )

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is False

    def test_action_cancel_event_marks_event_cancelled(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """cancel_event marca el evento como cancelado en la DB."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.calendar_tracker.models.event import Event

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        event = db.query(Event).filter(Event.id == event_id).first()
        assert event.is_cancelled is False

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.cancel_event",
            action_config={"event_id": event_id},
            payload={"event_id": event_id},
            user_id=automation.user_id,
        )

        assert execution.status.value == "success"
        db.refresh(event)
        assert event.is_cancelled is True

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is True
        assert action_log["output"]["cancelled"] is True
        assert action_log["output"]["event_id"] == event_id

    def test_action_cancel_event_nonexistent_returns_false(
        self, db, auth_client, event_id, automation_for_event_start
    ):
        """cancel_event con evento inexistente devuelve cancelled=False sin explotar."""
        from app.modules.automations_engine.models.automation import Automation

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.cancel_event",
            action_config={"event_id": 99999},
            payload={"event_id": event_id},
            user_id=automation.user_id,
        )

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is False

    def test_action_push_summary_overdue_returns_summary(
        self, db, auth_client, overdue_reminder_id, automation_for_overdue
    ):
        """push_summary_overdue devuelve un resumen con los recordatorios vencidos."""
        from app.modules.automations_engine.models.automation import Automation

        automation = db.query(Automation).filter(
            Automation.id == automation_for_overdue
        ).first()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.overdue_reminders_exist",
            action_id="calendar_tracker.push_summary_overdue",
            action_config={"min_priority": "low"},
            payload={},
            user_id=automation.user_id,
        )

        assert execution.status.value == "success"
        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["count"] >= 1
        assert len(action_log["output"]["reminders"]) >= 1
        assert "summary" in action_log["output"]
        assert action_log["output"]["summary"] != "No hay recordatorios vencidos."

    def test_action_get_todays_schedule_returns_events(
        self, db, auth_client, event_starting_now, automation_for_event_start
    ):
        """get_todays_schedule devuelve los eventos de hoy."""
        from app.modules.automations_engine.models.automation import Automation

        automation = db.query(Automation).filter(
            Automation.id == automation_for_event_start
        ).first()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.event_start",
            action_id="calendar_tracker.get_todays_schedule",
            action_config={},
            payload={"event_id": event_starting_now},
            user_id=automation.user_id,
        )

        assert execution.status.value == "success"
        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["count"] >= 1
        assert isinstance(action_log["output"]["events"], list)
        assert "summary_text" in action_log["output"]

    def test_action_bulk_mark_overdue_done_marks_all(
        self, db, auth_client, automation_for_overdue
    ):
        """bulk_mark_overdue_done marca todos los recordatorios vencidos como DONE."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.calendar_tracker.models.reminder import Reminder
        from app.modules.calendar_tracker.enums import ReminderStatus

        automation = db.query(Automation).filter(
            Automation.id == automation_for_overdue
        ).first()
        user_id = automation.user_id

        # Crear 3 recordatorios vencidos
        for i in range(3):
            auth_client.post("/api/v1/calendar/reminders", json={
                "title":    f"Vencido {i}",
                "priority": "medium",
                "due_date": (date.today() - timedelta(days=i + 1)).isoformat(),
            })

        pending_before = db.query(Reminder).filter(
            Reminder.user_id == user_id,
            Reminder.status  == ReminderStatus.PENDING,
        ).count()
        assert pending_before >= 3

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.overdue_reminders_exist",
            action_id="calendar_tracker.bulk_mark_overdue_done",
            action_config={"min_priority": "low"},
            payload={},
            user_id=user_id,
        )

        assert execution.status.value == "success"
        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["marked_done"] >= 3

        pending_after = db.query(Reminder).filter(
            Reminder.user_id == user_id,
            Reminder.status  == ReminderStatus.PENDING,
            Reminder.due_date < date.today(),
        ).count()
        assert pending_after == 0

    def test_action_bulk_mark_overdue_done_respects_min_priority(
        self, db, auth_client, automation_for_overdue
    ):
        """bulk_mark_overdue_done respeta la prioridad mínima configurada."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.calendar_tracker.models.reminder import Reminder
        from app.modules.calendar_tracker.enums import ReminderStatus

        automation = db.query(Automation).filter(
            Automation.id == automation_for_overdue
        ).first()
        user_id = automation.user_id

        # Crear uno low y uno high
        auth_client.post("/api/v1/calendar/reminders", json={
            "title": "Low priority", "priority": "low",
            "due_date": (date.today() - timedelta(days=1)).isoformat(),
        })
        auth_client.post("/api/v1/calendar/reminders", json={
            "title": "High priority", "priority": "high",
            "due_date": (date.today() - timedelta(days=1)).isoformat(),
        })

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="calendar_tracker.overdue_reminders_exist",
            action_id="calendar_tracker.bulk_mark_overdue_done",
            action_config={"min_priority": "high"},
            payload={},
            user_id=user_id,
        )

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        # Solo debe marcar el high, no el low
        assert action_log["output"]["marked_done"] == 1
        assert "High priority" in action_log["output"]["titles"]
        assert "Low priority" not in action_log["output"]["titles"]