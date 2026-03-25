"""
Scheduler de expenses_tracker.
Detecta suscripciones próximas a vencer y presupuestos mensuales superados,
y dispara automatizaciones.

Se ejecuta una vez al día via APScheduler.
Es completamente independiente del motor de automatizaciones —
si automation_dispatcher.py no existe, el scheduler sigue funcionando.
"""
import logging
from datetime import date, datetime, timezone, timedelta

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# ── Deduplicación en memoria ──────────────────────────────────────────────────
# Evita disparar el mismo trigger dos veces en el mismo día para el mismo objeto.
_subscription_due_cache: dict[tuple, date] = {}   # (scheduled_id, "YYYY-MM-DD") -> dispatched_date
_budget_exceeded_cache: dict[tuple, str]  = {}    # (user_id, "YYYY-MM") -> dispatched_month


def _get_db():
    return SessionLocal()


def _try_dispatch(method_name: str, *args, **kwargs) -> None:
    """
    Llama al dispatcher de automatizaciones si existe.
    Si el módulo no está instalado o falla, se ignora silenciosamente.
    """
    try:
        from .automation_dispatcher import dispatcher
        getattr(dispatcher, method_name)(*args, **kwargs)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"automation_dispatcher.{method_name} falló: {e}")


def job_check_subscription_due_soon() -> None:
    """
    Detecta suscripciones activas cuya fecha de pago cae en los próximos 1-30 días
    y dispara automatizaciones suscritas a expenses_tracker.subscription_due_soon.
    La deduplicación evita disparar el mismo trigger más de una vez por día.
    """
    db = _get_db()
    try:
        from .scheduled_expense_model import ScheduledExpense, ScheduledCategory

        today  = date.today()
        cutoff = today + timedelta(days=30)

        items = db.query(ScheduledExpense).filter(
            ScheduledExpense.is_active         == True,
            ScheduledExpense.next_payment_date != None,
            ScheduledExpense.next_payment_date >  today,
            ScheduledExpense.next_payment_date <= cutoff,
            ScheduledExpense.category          == ScheduledCategory.SUBSCRIPTION,
        ).all()

        for item in items:
            due_key = (item.id, item.next_payment_date.isoformat())
            if _subscription_due_cache.get(due_key) == today:
                continue  # ya despachado hoy

            days_until = (item.next_payment_date - today).days
            logger.info(
                f"Suscripción próxima: '{item.name}' (id={item.id}, "
                f"user={item.user_id}, days_until={days_until})"
            )
            _subscription_due_cache[due_key] = today
            _try_dispatch(
                "on_subscription_due_soon",
                scheduled_id=item.id,
                name=item.name,
                amount=item.amount,
                due_date=item.next_payment_date.isoformat(),
                days_until=days_until,
                user_id=item.user_id,
                db=db,
            )

    except Exception as e:
        logger.error(f"job_check_subscription_due_soon error: {e}")
    finally:
        db.close()


def job_check_monthly_budget() -> None:
    """
    Comprueba si algún usuario ha superado el límite mensual configurado en sus
    automatizaciones suscritas a expenses_tracker.monthly_budget_exceeded.

    Itera las automatizaciones activas con ese trigger_ref, lee su config para
    saber el límite y cuenta, y comprueba si el total del mes actual supera el límite.
    Deduplicación: solo dispara una vez por (user_id, "YYYY-MM").
    """
    db = _get_db()
    try:
        from app.modules.automations_engine.models.automation import Automation
        from .expense import Expense

        today       = date.today()
        month_key   = today.strftime("%Y-%m")
        month_start = datetime(today.year, today.month, 1, tzinfo=timezone.utc)
        if today.month == 12:
            month_end = datetime(today.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            month_end = datetime(today.year, today.month + 1, 1, tzinfo=timezone.utc)

        automations = db.query(Automation).filter(
            Automation.trigger_ref == "expenses_tracker.monthly_budget_exceeded",
            Automation.is_active   == True,
        ).all()

        for automation in automations:
            user_id = automation.user_id

            dedup_key = (user_id, month_key)
            if _budget_exceeded_cache.get(dedup_key) == month_key:
                continue  # ya despachado este mes

            # Extraer config del nodo trigger del flow
            flow    = automation.flow or {}
            nodes   = flow.get("nodes", [])
            trigger_node = next(
                (n for n in nodes if n.get("type") == "trigger"), None
            )
            config = trigger_node.get("config", {}) if trigger_node else {}

            limit        = float(config.get("limit", 1000.0))
            account_cfg  = config.get("account", "all")

            # Calcular total mensual del usuario
            query = db.query(Expense).filter(
                Expense.user_id    == user_id,
                Expense.created_at >= month_start,
                Expense.created_at <  month_end,
            )
            if account_cfg != "all":
                from .enums.expense_category import ExpenseCategory
                try:
                    acct_enum = ExpenseCategory(account_cfg)
                    query = query.filter(Expense.account == acct_enum)
                except ValueError:
                    pass

            expenses = query.all()
            total    = sum(e.quantity for e in expenses)

            if total >= limit:
                logger.info(
                    f"Presupuesto superado para user {user_id}: "
                    f"{total:.2f} >= {limit:.2f} ({account_cfg}, {month_key})"
                )
                _budget_exceeded_cache[dedup_key] = month_key
                _try_dispatch(
                    "on_monthly_budget_exceeded",
                    total=round(total, 2),
                    month=month_key,
                    account=account_cfg,
                    user_id=user_id,
                    db=db,
                )

    except Exception as e:
        logger.error(f"job_check_monthly_budget error: {e}")
    finally:
        db.close()
