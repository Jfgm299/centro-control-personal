# app/modules/expenses_tracker/__init__.py
from .expenses_router import router
#from .handlers.expenses_handlers import register_exception_handlers as register_handlers

TAGS = [{"name": "expenses", "description": "Gestión de gastos personales"}]
TAG_GROUP = {"name": "Expenses", "tags": ["Expenses"]}


def start_expenses_scheduler() -> None:
    from apscheduler.schedulers.background import BackgroundScheduler
    import logging as _logging
    from .scheduler_service import (
        job_check_subscription_due_soon,
        job_check_monthly_budget,
    )

    scheduler = BackgroundScheduler(timezone="UTC")

    # Suscripciones próximas — una vez al día a las 8:00 UTC
    scheduler.add_job(job_check_subscription_due_soon, "cron", hour=8, id="expenses_subscription_due")
    # Presupuesto mensual superado — una vez al día a las 8:05 UTC
    scheduler.add_job(job_check_monthly_budget,        "cron", hour=8, minute=5, id="expenses_monthly_budget")

    scheduler.start()
    _logging.getLogger(__name__).info("✅ Expenses scheduler iniciado")


__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP", "start_expenses_scheduler"]