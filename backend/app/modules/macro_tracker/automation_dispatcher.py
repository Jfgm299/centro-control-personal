"""
Dispatcher de automatizaciones para macro_tracker.

Conecta los eventos de diary_service (hooks en add_entry y upsert_goals) y del
scheduler con el motor de automatizaciones.
Este archivo es completamente opcional — si se elimina, los servicios siguen
funcionando y solo dejan de disparar automatizaciones.

TRIGGERS que despacha:
    macro_tracker.meal_logged              — Comida registrada
    macro_tracker.daily_macro_threshold    — % de macro diario superado/bajo
    macro_tracker.goal_updated             — Objetivos actualizados
    macro_tracker.no_entry_logged_today    — Sin entradas hoy a cierta hora
    macro_tracker.logging_streak           — N días consecutivos
"""
import logging
from datetime import date
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MACRO_FIELDS = ["energy_kcal", "proteins_g", "carbohydrates_g", "fat_g", "fiber_g"]

# Dedup para daily_macro_threshold: (user_id, date_str, macro, direction)
_macro_threshold_cache: set = set()


class MacroAutomationDispatcher:

    def _find_and_execute(self, trigger_ref: str, payload: dict, user_id: int, db: Session) -> None:
        try:
            from app.modules.automations_engine.models.automation import Automation
            from app.modules.automations_engine.services.flow_executor import flow_executor
            from app.modules.automations_engine.services.execution_service import execution_service
            from datetime import datetime, timezone

            automations = db.query(Automation).filter(
                Automation.trigger_ref == trigger_ref,
                Automation.user_id     == user_id,
                Automation.is_active   == True,
            ).all()

            for automation in automations:
                try:
                    logger.info(
                        f"Disparando automatización '{automation.name}' "
                        f"(id={automation.id}) via {trigger_ref}"
                    )
                    execution = execution_service.create(automation.id, user_id, payload, db)
                    execution = execution_service.mark_running(execution, db)

                    result = flow_executor.execute(automation, payload, db, user_id)

                    if result["status"] == "success":
                        execution_service.mark_success(execution, result["node_logs"], db)
                    else:
                        execution_service.mark_failed(
                            execution, result.get("error", ""), result["node_logs"], db
                        )

                    automation.last_run_at = datetime.now(timezone.utc)
                    automation.run_count   = (automation.run_count or 0) + 1
                    db.commit()

                    logger.info(
                        f"Automatización '{automation.name}' terminó con status={result['status']}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error ejecutando automatización '{automation.name}' "
                        f"(id={automation.id}): {e}"
                    )

        except ImportError:
            pass
        except Exception as e:
            logger.error(f"_find_and_execute({trigger_ref}) error: {e}")

    def on_meal_logged(self, entry_id: int, user_id: int, db: Session) -> None:
        """
        Llamado por diary_service.add_entry() tras db.refresh().
        Despacha macro_tracker.meal_logged.
        El payload es mínimo — el handler carga entry + product desde BD.
        """
        self._find_and_execute(
            trigger_ref="macro_tracker.meal_logged",
            payload={"entry_id": entry_id},
            user_id=user_id,
            db=db,
        )

    def on_entry_added_check_threshold(self, entry_id: int, user_id: int, db: Session) -> None:
        """
        Llamado por diary_service.add_entry() tras db.refresh().
        Comprueba los 5 macros contra UserGoal para los triggers daily_macro_threshold.
        Dedup: (user_id, date_str, macro, direction) — una vez por combo por día.

        Estrategia:
        1. Calcular totales diarios del usuario
        2. Obtener UserGoal — salir si no hay
        3. Para cada automation activa con trigger_ref=daily_macro_threshold:
           a. Extraer config (macro, threshold_pct, direction)
           b. Comprobar dedup
           c. Calcular progress_pct
           d. Si condición → disparar con payload pre-construido
        """
        try:
            from app.modules.automations_engine.models.automation import Automation
            from .diary_entry import DiaryEntry
            from .user_goal import UserGoal

            today     = date.today()
            today_str = str(today)

            entries = db.query(DiaryEntry).filter(
                DiaryEntry.user_id    == user_id,
                DiaryEntry.entry_date == today,
            ).all()

            totals = {f: sum(getattr(e, f) or 0.0 for e in entries) for f in MACRO_FIELDS}

            goal = db.query(UserGoal).filter(UserGoal.user_id == user_id).first()
            if not goal:
                return

            automations = db.query(Automation).filter(
                Automation.trigger_ref == "macro_tracker.daily_macro_threshold",
                Automation.user_id     == user_id,
                Automation.is_active   == True,
            ).all()

            for automation in automations:
                flow         = automation.flow or {}
                nodes        = flow.get("nodes", [])
                trigger_node = next((n for n in nodes if n.get("type") == "trigger"), None)
                config       = trigger_node.get("config", {}) if trigger_node else {}

                macro         = config.get("macro")
                threshold_pct = float(config.get("threshold_pct", 100))
                direction     = config.get("direction", "above")

                if not macro or macro not in MACRO_FIELDS:
                    continue

                dedup_key = (user_id, today_str, macro, direction)
                if dedup_key in _macro_threshold_cache:
                    continue

                goal_val = getattr(goal, macro, None)
                if not goal_val:
                    continue

                actual       = totals.get(macro, 0.0)
                progress_pct = round(actual / goal_val * 100, 1)

                condition_met = (
                    (direction == "above" and progress_pct >= threshold_pct) or
                    (direction == "below" and progress_pct <= threshold_pct)
                )
                if not condition_met:
                    continue

                _macro_threshold_cache.add(dedup_key)

                self._find_and_execute(
                    trigger_ref="macro_tracker.daily_macro_threshold",
                    payload={
                        "date":         today_str,
                        "macro":        macro,
                        "actual_value": round(actual, 2),
                        "goal_value":   goal_val,
                        "progress_pct": progress_pct,
                    },
                    user_id=user_id,
                    db=db,
                )

        except ImportError:
            pass
        except Exception as e:
            logger.error(f"on_entry_added_check_threshold error: {e}")

    def on_goal_updated(
        self,
        user_id: int,
        old_snapshot: dict | None,
        new_goal,
        db: Session,
    ) -> None:
        """
        Llamado por diary_service.upsert_goals() TRAS commit + refresh.
        old_snapshot: dict de {macro: value} ANTES del upsert, o None si es primera creación.
        Calcula changed_fields comparando old_snapshot vs new_goal.
        """
        try:
            if old_snapshot is None:
                # Primera creación — todos los campos no-None se consideran "cambiados"
                changed_fields = [
                    f for f in MACRO_FIELDS
                    if getattr(new_goal, f) is not None
                ]
            else:
                changed_fields = [
                    f for f in MACRO_FIELDS
                    if old_snapshot.get(f) != getattr(new_goal, f)
                ]

            if not changed_fields:
                return

            payload = {f: getattr(new_goal, f) for f in MACRO_FIELDS}
            payload["changed_fields"] = changed_fields

            self._find_and_execute(
                trigger_ref="macro_tracker.goal_updated",
                payload=payload,
                user_id=user_id,
                db=db,
            )

        except Exception as e:
            logger.error(f"on_goal_updated error: {e}")

    def on_no_entry_logged_today(
        self,
        user_id: int,
        days_since_last: int,
        last_entry_date: str | None,
        db: Session,
    ) -> None:
        """Llamado por el scheduler tras verificar hora y dedup."""
        self._find_and_execute(
            trigger_ref="macro_tracker.no_entry_logged_today",
            payload={
                "days_since_last_entry": days_since_last,
                "last_entry_date":       last_entry_date,
            },
            user_id=user_id,
            db=db,
        )

    def on_logging_streak(
        self,
        user_id: int,
        streak_days: int,
        streak_start_date: str,
        db: Session,
    ) -> None:
        """Llamado por el scheduler tras verificar la coincidencia exacta de racha."""
        self._find_and_execute(
            trigger_ref="macro_tracker.logging_streak",
            payload={
                "streak_days":       streak_days,
                "streak_start_date": streak_start_date,
            },
            user_id=user_id,
            db=db,
        )


dispatcher = MacroAutomationDispatcher()
