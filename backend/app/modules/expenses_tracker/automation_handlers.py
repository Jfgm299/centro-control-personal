"""
Handlers de automatizaciones para expenses_tracker.
Contrato: handler(payload, config, db, user_id) -> dict

TRIGGERS:
    handle_large_expense_created    — Gasto creado por encima de un umbral
    handle_monthly_budget_exceeded  — Total mensual supera un límite
    handle_subscription_due_soon    — Suscripción vence en N días
    handle_subscription_converted   — Suscripción vencida convertida en gasto real

ACCIONES:
    action_create_expense             — Crear gasto puntual
    action_get_monthly_summary        — Totales mensuales por cuenta
    action_get_upcoming_subscriptions — Suscripciones activas próximas
"""
from datetime import date, datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from .expense import Expense
from .scheduled_expense_model import ScheduledExpense, ScheduledCategory
from .enums.expense_category import ExpenseCategory


# ── Utilidades internas ───────────────────────────────────────────────────────

def _expense_to_dict(expense: Expense) -> dict:
    return {
        "id":         expense.id,
        "name":       expense.name,
        "amount":     expense.quantity,
        "account":    expense.account.value if expense.account else None,
        "created_at": expense.created_at.isoformat() if expense.created_at else None,
    }


def _scheduled_to_dict(item: ScheduledExpense) -> dict:
    return {
        "id":                item.id,
        "name":              item.name,
        "amount":            item.amount,
        "account":           item.account.value if item.account else None,
        "frequency":         item.frequency.value if item.frequency else None,
        "category":          item.category.value if item.category else None,
        "next_payment_date": item.next_payment_date.isoformat() if item.next_payment_date else None,
        "is_active":         item.is_active,
    }


# ── TRIGGER HANDLERS ──────────────────────────────────────────────────────────

def handle_large_expense_created(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando se crea un gasto por encima del umbral configurado.
    Payload esperado: {"expense_id": int, "amount": float, "account": str}
    Config:
        - min_amount: float  — umbral mínimo (default 100.0)
        - account: str       — filtrar por cuenta (opcional)
    """
    expense_id = payload.get("expense_id")
    if not expense_id:
        return {"matched": False, "reason": "no expense_id in payload"}

    expense = db.query(Expense).filter(
        Expense.id      == expense_id,
        Expense.user_id == user_id,
    ).first()

    if not expense:
        return {"matched": False, "reason": f"expense {expense_id} not found"}

    min_amount = config.get("min_amount", 100.0)
    if expense.quantity < min_amount:
        return {
            "matched": False,
            "reason":  f"amount {expense.quantity} below threshold {min_amount}",
        }

    filter_account = config.get("account")
    if filter_account and expense.account.value != filter_account:
        return {
            "matched": False,
            "reason":  f"account {expense.account.value} not matching filter {filter_account}",
        }

    return {"matched": True, "expense": _expense_to_dict(expense)}


def handle_monthly_budget_exceeded(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando el total del mes actual supera el límite configurado.
    Payload esperado: {"total": float, "month": str, "account": str}
    Config:
        - limit: float  — límite mensual (default 1000.0)
        - account: str  — cuenta a controlar (default "all")
    """
    total   = payload.get("total", 0.0)
    limit   = config.get("limit", 1000.0)
    account = config.get("account", "all")

    payload_account = payload.get("account", "all")

    # Si la config filtra por cuenta y el payload es de otra, no disparar
    if account != "all" and payload_account != "all" and account != payload_account:
        return {
            "matched": False,
            "reason":  f"account filter mismatch: config={account}, payload={payload_account}",
        }

    if total < limit:
        return {
            "matched": False,
            "reason":  f"total {total:.2f} below limit {limit:.2f}",
        }

    return {
        "matched": True,
        "total":   total,
        "limit":   limit,
        "month":   payload.get("month", ""),
        "account": payload_account,
    }


def handle_subscription_due_soon(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando una suscripción vence en N días.
    Payload esperado: {"scheduled_id": int, "name": str, "amount": float, "due_date": str, "days_until": int}
    Config:
        - days_ahead: int  — máximo de días de antelación (default 3)
    """
    scheduled_id = payload.get("scheduled_id")
    if not scheduled_id:
        return {"matched": False, "reason": "no scheduled_id in payload"}

    item = db.query(ScheduledExpense).filter(
        ScheduledExpense.id      == scheduled_id,
        ScheduledExpense.user_id == user_id,
        ScheduledExpense.is_active == True,
    ).first()

    if not item:
        return {"matched": False, "reason": f"scheduled expense {scheduled_id} not found or inactive"}

    days_ahead = config.get("days_ahead", 3)
    days_until = payload.get("days_until", 0)

    if days_until > days_ahead:
        return {
            "matched": False,
            "reason":  f"due in {days_until} days, threshold is {days_ahead}",
        }

    return {
        "matched":    True,
        "subscription": _scheduled_to_dict(item),
        "days_until": days_until,
    }


def handle_subscription_converted(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando una suscripción vencida se convierte automáticamente en gasto real.
    Payload esperado: {"scheduled_id": int, "expense_id": int, "name": str, "amount": float}
    """
    scheduled_id = payload.get("scheduled_id")
    expense_id   = payload.get("expense_id")

    if not scheduled_id or not expense_id:
        return {"matched": False, "reason": "missing scheduled_id or expense_id in payload"}

    expense = db.query(Expense).filter(
        Expense.id      == expense_id,
        Expense.user_id == user_id,
    ).first()

    if not expense:
        return {"matched": False, "reason": f"expense {expense_id} not found"}

    return {
        "matched":      True,
        "expense":      _expense_to_dict(expense),
        "scheduled_id": scheduled_id,
        "name":         payload.get("name", expense.name),
        "amount":       payload.get("amount", expense.quantity),
    }


# ── ACTION HANDLERS ───────────────────────────────────────────────────────────

def action_create_expense(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: crear un gasto puntual.
    Config:
        - name: str                   — nombre del gasto
        - amount: float               — importe
        - account: str                — Revolut | Imagin (default "Revolut")
    """
    name    = config.get("name", payload.get("name", "Gasto automático"))
    amount  = config.get("amount", payload.get("amount", 0.0))
    account_str = config.get("account", "Revolut")

    try:
        account = ExpenseCategory(account_str)
    except ValueError:
        account = ExpenseCategory.REVOLUT

    expense = Expense(
        user_id  = user_id,
        name     = name,
        quantity = amount,
        account  = account,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    return {"done": True, "expense": _expense_to_dict(expense)}


def action_get_monthly_summary(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: obtener totales mensuales por cuenta.
    Config:
        - month_offset: int  — 0=mes actual, -1=mes anterior, etc. (default 0)
    """
    month_offset = config.get("month_offset", 0)

    today       = date.today()
    target_date = today.replace(day=1)
    # Aplicar offset de meses
    if month_offset < 0:
        for _ in range(abs(month_offset)):
            target_date = (target_date - timedelta(days=1)).replace(day=1)
    elif month_offset > 0:
        for _ in range(month_offset):
            # Avanzar al primer día del mes siguiente
            if target_date.month == 12:
                target_date = target_date.replace(year=target_date.year + 1, month=1)
            else:
                target_date = target_date.replace(month=target_date.month + 1)

    # Calcular el rango del mes target
    month_start = target_date
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1)

    expenses = db.query(Expense).filter(
        Expense.user_id    == user_id,
        Expense.created_at >= datetime(month_start.year, month_start.month, 1, tzinfo=timezone.utc),
        Expense.created_at <  datetime(month_end.year,  month_end.month,   1, tzinfo=timezone.utc),
    ).all()

    total_by_account: dict[str, float] = {}
    grand_total = 0.0

    for exp in expenses:
        acct = exp.account.value if exp.account else "unknown"
        total_by_account[acct] = total_by_account.get(acct, 0.0) + exp.quantity
        grand_total += exp.quantity

    return {
        "done":             True,
        "month":            month_start.strftime("%Y-%m"),
        "grand_total":      round(grand_total, 2),
        "total_by_account": {k: round(v, 2) for k, v in total_by_account.items()},
        "count":            len(expenses),
    }


def action_get_upcoming_subscriptions(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: listar suscripciones activas con fecha de pago próxima.
    Config:
        - days_ahead: int  — días hacia adelante (default 30)
    """
    days_ahead = config.get("days_ahead", 30)
    today      = date.today()
    cutoff     = today + timedelta(days=days_ahead)

    items = db.query(ScheduledExpense).filter(
        ScheduledExpense.user_id           == user_id,
        ScheduledExpense.is_active         == True,
        ScheduledExpense.next_payment_date != None,
        ScheduledExpense.next_payment_date <= cutoff,
    ).order_by(ScheduledExpense.next_payment_date.asc()).all()

    result = []
    for item in items:
        d = _scheduled_to_dict(item)
        if item.next_payment_date:
            d["days_until"] = (item.next_payment_date - today).days
        result.append(d)

    return {
        "done":          True,
        "count":         len(result),
        "subscriptions": result,
    }
