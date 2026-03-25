"""
Handlers de automatizaciones para calendar_tracker.
Contrato: handler(payload, config, db, user_id) -> dict
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from ..models.event import Event
from ..models.reminder import Reminder
from ..enums import ReminderStatus, ReminderPriority



"""
Implementación de triggers y acciones de calendar_tracker para el motor de automatizaciones.
Cada función sigue el contrato: handler(payload, config, db, user_id) -> dict

TRIGGERS:
    handle_event_start            — Al iniciar un evento. Filtra por categoría y DND.
    handle_event_end              — Al finalizar un evento. Filtra por categoría.
    handle_reminder_due           — Cuando vence un recordatorio. Filtra por prioridad mínima.
    handle_no_events_in_window    — Cuando no hay eventos en una ventana de tiempo futura.
    handle_overdue_reminders_exist — Cuando existen N o más recordatorios vencidos pendientes.

ACCIONES:
    action_create_event           — Crea un evento con título, duración, categoría y DND configurables.
    action_create_reminder        — Crea un recordatorio con prioridad y fecha de vencimiento.
    action_mark_reminder_done     — Marca un recordatorio específico como completado.
    action_cancel_event           — Cancela un evento específico.
    action_push_summary_overdue   — Construye un resumen de texto de recordatorios vencidos.
    action_get_todays_schedule    — Devuelve todos los eventos del día en el contexto del flujo.
    action_bulk_mark_overdue_done — Marca en bloque todos los recordatorios vencidos como completados.
"""


# ── Utilidades internas ───────────────────────────────────────────────────────

_PRIORITY_ORDER = {
    ReminderPriority.LOW:    0,
    ReminderPriority.MEDIUM: 1,
    ReminderPriority.HIGH:   2,
    ReminderPriority.URGENT: 3,
}

_PRIORITY_MAP = {
    "low":    ReminderPriority.LOW,
    "medium": ReminderPriority.MEDIUM,
    "high":   ReminderPriority.HIGH,
    "urgent": ReminderPriority.URGENT,
}

def _event_to_dict(event: Event) -> dict:
    return {
        "id":               event.id,
        "title":            event.title,
        "description":      event.description,
        "start_at":         event.start_at.isoformat() if event.start_at else None,
        "end_at":           event.end_at.isoformat()   if event.end_at   else None,
        "all_day":          event.all_day,
        "enable_dnd":       event.enable_dnd,
        "category_id":      event.category_id,
        "reminder_minutes": event.reminder_minutes,
    }

def _reminder_to_dict(reminder: Reminder) -> dict:
    return {
        "id":          reminder.id,
        "title":       reminder.title,
        "description": reminder.description,
        "status":      reminder.status.value,
        "priority":    reminder.priority.value,
        "due_date":    reminder.due_date.isoformat() if reminder.due_date else None,
        "category_id": reminder.category_id,
    }


# ── TRIGGER HANDLERS ──────────────────────────────────────────────────────────

def handle_event_start(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: al iniciar un evento.
    Payload esperado: {"event_id": int}
    Config opcional:
        - category_ids: list[int]  — solo disparar si el evento pertenece a estas categorías
        - enable_dnd_only: bool    — solo disparar si el evento tiene DND activo
        - advance_minutes: int     — ya fue aplicado por quien disparó el trigger
    """
    event_id = payload.get("event_id")
    if not event_id:
        return {"matched": False, "reason": "no event_id in payload"}

    event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == user_id,
        Event.is_cancelled == False,
    ).first()

    if not event:
        return {"matched": False, "reason": f"event {event_id} not found"}

    category_ids = config.get("category_ids")
    if category_ids and event.category_id not in category_ids:
        return {"matched": False, "reason": "category not in filter"}

    if config.get("enable_dnd_only") and not event.enable_dnd:
        return {"matched": False, "reason": "event does not have DND enabled"}

    return {"matched": True, "event": _event_to_dict(event)}


def handle_event_end(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: al finalizar un evento.
    Payload esperado: {"event_id": int}
    """
    event_id = payload.get("event_id")
    if not event_id:
        return {"matched": False, "reason": "no event_id in payload"}

    event = db.query(Event).filter(
        Event.id == event_id,
        Event.user_id == user_id,
    ).first()

    if not event:
        return {"matched": False, "reason": f"event {event_id} not found"}

    category_ids = config.get("category_ids")
    if category_ids and event.category_id not in category_ids:
        return {"matched": False, "reason": "category not in filter"}

    return {"matched": True, "event": _event_to_dict(event)}


def handle_reminder_due(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando vence un recordatorio.
    Payload esperado: {"reminder_id": int}
    Config opcional:
        - min_priority: str (low|medium|high|urgent)
    """
    reminder_id = payload.get("reminder_id")
    if not reminder_id:
        return {"matched": False, "reason": "no reminder_id in payload"}

    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.user_id == user_id,
    ).first()

    if not reminder:
        return {"matched": False, "reason": f"reminder {reminder_id} not found"}

    min_priority_str = config.get("min_priority", "high")
    min_priority     = _PRIORITY_MAP.get(min_priority_str, ReminderPriority.HIGH)

    if _PRIORITY_ORDER[reminder.priority] < _PRIORITY_ORDER[min_priority]:
        return {"matched": False, "reason": f"priority {reminder.priority.value} below minimum {min_priority_str}"}

    return {"matched": True, "reminder": _reminder_to_dict(reminder)}


def handle_no_events_in_window(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando no hay eventos en una ventana de tiempo futura.
    Útil para detectar tiempo libre y disparar acciones.
    Config:
        - window_hours: int   — cuántas horas hacia adelante mirar (default 2)
        - min_free_minutes: int — mínimo de minutos libres requeridos (default 60)
    """
    window_hours     = config.get("window_hours", 2)
    min_free_minutes = config.get("min_free_minutes", 60)

    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=window_hours)

    # Incluye eventos que ya empezaron pero aún no han terminado (en curso)
    events = db.query(Event).filter(
        Event.user_id      == user_id,
        Event.is_cancelled == False,
        Event.start_at     <= end,   # empieza antes del fin de la ventana
        Event.end_at       >= now,   # todavía no ha terminado
    ).all()

    if events:
        return {"matched": False, "reason": f"found {len(events)} events in window", "events_count": len(events)}

    free_minutes = window_hours * 60
    if free_minutes < min_free_minutes:
        return {"matched": False, "reason": "not enough free time"}

    return {
        "matched":      True,
        "free_minutes": free_minutes,
        "window_start": now.isoformat(),
        "window_end":   end.isoformat(),
    }

def handle_overdue_reminders_exist(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando existen recordatorios vencidos sin programar.
    Config:
        - min_count: int       — mínimo de recordatorios vencidos para disparar (default 1)
        - min_priority: str    — prioridad mínima a considerar (default "medium")
    """
    min_count        = config.get("min_count", 1)
    min_priority_str = config.get("min_priority", "medium")
    min_priority     = _PRIORITY_MAP.get(min_priority_str, ReminderPriority.MEDIUM)

    today = datetime.now(timezone.utc).date()

    overdue = db.query(Reminder).filter(
        Reminder.user_id == user_id,
        Reminder.status == ReminderStatus.PENDING,
        Reminder.due_date < today,
    ).all()

    filtered = [
        r for r in overdue
        if _PRIORITY_ORDER[r.priority] >= _PRIORITY_ORDER[min_priority]
    ]

    if len(filtered) < min_count:
        return {"matched": False, "reason": f"only {len(filtered)} overdue reminders, need {min_count}"}

    return {
        "matched":          True,
        "overdue_count":    len(filtered),
        "overdue_reminders": [_reminder_to_dict(r) for r in filtered],
    }


# ── ACTION HANDLERS ───────────────────────────────────────────────────────────

def action_create_event(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: crear un evento en el calendario.
    Config:
        - title: str                  — soporta template {{ vars.X }} resuelto antes de llegar aquí
        - duration_minutes: int       — duración (default 30)
        - category_id: int            — opcional
        - enable_dnd: bool            — default False
        - reminder_minutes: int       — opcional
        - start_offset_minutes: int   — minutos desde ahora para el inicio (default 0)
    """
    from datetime import datetime, timezone, timedelta

    title            = config.get("title", payload.get("title", "Evento automático"))
    duration_minutes = config.get("duration_minutes", 30)
    category_id      = config.get("category_id")
    enable_dnd       = config.get("enable_dnd", False)
    reminder_minutes = config.get("reminder_minutes")
    start_offset     = config.get("start_offset_minutes", 0)

    now      = datetime.now(timezone.utc)
    start_at = now + timedelta(minutes=start_offset)
    end_at   = start_at + timedelta(minutes=duration_minutes)

    event = Event(
        user_id          = user_id,
        title            = title,
        category_id      = category_id,
        start_at         = start_at,
        end_at           = end_at,
        all_day          = False,
        enable_dnd       = enable_dnd,
        reminder_minutes = reminder_minutes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {"created": True, "event": _event_to_dict(event)}


def action_create_reminder(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: crear un recordatorio.
    Config:
        - title: str
        - description: str          — opcional
        - priority: str             — low|medium|high|urgent (default "medium")
        - category_id: int          — opcional
        - due_in_days: int          — días desde hoy para el vencimiento (default None)
    """
    from datetime import date, timedelta

    title       = config.get("title", payload.get("title", "Recordatorio automático"))
    description = config.get("description")
    priority    = _PRIORITY_MAP.get(config.get("priority", "medium"), ReminderPriority.MEDIUM)
    category_id = config.get("category_id")
    due_in_days = config.get("due_in_days")
    due_date    = date.today() + timedelta(days=due_in_days) if due_in_days is not None else None

    reminder = Reminder(
        user_id     = user_id,
        title       = title,
        description = description,
        priority    = priority,
        category_id = category_id,
        due_date    = due_date,
        status      = ReminderStatus.PENDING,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    return {"created": True, "reminder": _reminder_to_dict(reminder)}


def action_mark_reminder_done(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: marcar un recordatorio como completado.
    Config:
        - reminder_id: int   — si no está en config, lo busca en payload
    """
    reminder_id = config.get("reminder_id") or payload.get("reminder_id")
    if not reminder_id:
        return {"done": False, "reason": "no reminder_id provided"}

    reminder = db.query(Reminder).filter(
        Reminder.id      == reminder_id,
        Reminder.user_id == user_id,
    ).first()

    if not reminder:
        return {"done": False, "reason": f"reminder {reminder_id} not found"}

    reminder.status = ReminderStatus.DONE
    db.commit()

    return {"done": True, "reminder": _reminder_to_dict(reminder)}


def action_cancel_event(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: cancelar un evento.
    Config:
        - event_id: int   — si no está en config, lo busca en payload
    """
    event_id = config.get("event_id") or payload.get("event_id")
    if not event_id:
        return {"done": False, "reason": "no event_id provided"}

    event = db.query(Event).filter(
        Event.id         == event_id,
        Event.user_id    == user_id,
        Event.is_cancelled == False,
    ).first()

    if not event:
        return {"done": False, "reason": f"event {event_id} not found or already cancelled"}

    event.is_cancelled = True
    db.commit()

    return {"done": True, "cancelled": True, "event_id": event_id, "title": event.title}


def action_push_summary_overdue(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: construir un resumen de recordatorios vencidos y devolverlo en el contexto.
    Útil para que nodos posteriores (outbound_webhook, etc.) usen el resumen.
    Config:
        - max_items: int        — máximo de recordatorios a incluir (default 5)
        - min_priority: str     — prioridad mínima (default "medium")
    """
    max_items        = config.get("max_items", 5)
    min_priority_str = config.get("min_priority", "medium")
    min_priority     = _PRIORITY_MAP.get(min_priority_str, ReminderPriority.MEDIUM)

    today = datetime.now(timezone.utc).date()

    overdue = db.query(Reminder).filter(
        Reminder.user_id == user_id,
        Reminder.status  == ReminderStatus.PENDING,
        Reminder.due_date < today,
    ).order_by(Reminder.due_date).limit(max_items * 3).all()

    filtered = [
        r for r in overdue
        if _PRIORITY_ORDER[r.priority] >= _PRIORITY_ORDER[min_priority]
    ][:max_items]

    summary_lines = [
        f"- [{r.priority.value.upper()}] {r.title} (vencido: {r.due_date})"
        for r in filtered
    ]
    summary_text = "\n".join(summary_lines) if summary_lines else "No hay recordatorios vencidos."

    return {
        "done":          True,
        "summary":       summary_text,
        "count":         len(filtered),
        "reminders":     [_reminder_to_dict(r) for r in filtered],
    }


def action_get_todays_schedule(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: obtener el calendario de hoy y ponerlo en el contexto del flujo.
    Los nodos posteriores pueden usar vars.node_<id>.events para procesar.
    Config:
        - category_ids: list[int]  — filtrar por categorías (opcional)
        - include_cancelled: bool  — incluir cancelados (default False)
    """
    category_ids       = config.get("category_ids")
    include_cancelled  = config.get("include_cancelled", False)

    now   = datetime.now(timezone.utc)
    start = now.replace(hour=0,  minute=0,  second=0,  microsecond=0)
    end   = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    query = db.query(Event).filter(
        Event.user_id  == user_id,
        Event.start_at >= start,
        Event.start_at <= end,
    )

    if not include_cancelled:
        query = query.filter(Event.is_cancelled == False)

    if category_ids:
        query = query.filter(Event.category_id.in_(category_ids))

    events = query.order_by(Event.start_at).all()

    summary_lines = [
        f"- {e.title} ({e.start_at.strftime('%H:%M')} → {e.end_at.strftime('%H:%M')})"
        for e in events
    ]

    return {
        "done":         True,
        "events":       [_event_to_dict(e) for e in events],
        "count":        len(events),
        "summary_text": "\n".join(summary_lines) if summary_lines else "Sin eventos hoy.",
    }


def action_bulk_mark_overdue_done(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: marcar todos los recordatorios vencidos como completados de golpe.
    Config:
        - max_items: int       — máximo a marcar (default 20, safety cap)
        - min_priority: str    — solo marcar a partir de esta prioridad (default "low")
    """
    max_items        = config.get("max_items", 20)
    min_priority_str = config.get("min_priority", "low")
    min_priority     = _PRIORITY_MAP.get(min_priority_str, ReminderPriority.LOW)

    today = datetime.now(timezone.utc).date()

    overdue = db.query(Reminder).filter(
        Reminder.user_id == user_id,
        Reminder.status  == ReminderStatus.PENDING,
        Reminder.due_date < today,
    ).limit(max_items * 3).all()

    to_mark = [
        r for r in overdue
        if _PRIORITY_ORDER[r.priority] >= _PRIORITY_ORDER[min_priority]
    ][:max_items]

    for r in to_mark:
        r.status = ReminderStatus.DONE

    db.commit()

    return {
        "done":        True,
        "marked_done": len(to_mark),
        "titles":      [r.title for r in to_mark],
    }