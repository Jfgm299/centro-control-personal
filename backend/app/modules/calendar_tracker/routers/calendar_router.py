from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User

from ..schemas.calendar_schema import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    ReminderCreate,
    ReminderUpdate,
    ReminderSchedule,
    ReminderResponse,
    EventCreate,
    EventUpdate,
    EventResponse,
    RoutineCreate,
    RoutineUpdate,
    RoutineResponse,
    RoutineExceptionCreate,
    RoutineExceptionResponse,
    FcmTokenCreate,
    FcmTokenResponse,
)
from ..enums import ReminderStatus, ReminderPriority
from ..services import (
    CategoryService,
    ReminderService,
    EventService,
    RoutineService,
    NotificationService,
)
from ..models.fcm_token import FcmToken
from ..exceptions import FcmTokenNotFoundError

router = APIRouter(prefix="/calendar", tags=["Calendar"])

category_service     = CategoryService()
reminder_service     = ReminderService()
event_service        = EventService()
routine_service      = RoutineService()
notification_service = NotificationService()


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORIES
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/categories", response_model=list[CategoryResponse], tags=["Categories"])
def list_categories(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Lista todas las categorías del usuario ordenadas por nombre."""
    return category_service.get_all(db, user.id)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(
    data: CategoryCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Crea una categoría. Si no se especifica color, se asigna uno aleatorio de la paleta."""
    return category_service.create(db, user.id, data)


@router.patch("/categories/{category_id}", response_model=CategoryResponse, tags=["Categories"])
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Actualiza nombre, color, icono o defaults de DND/recordatorio de una categoría."""
    return category_service.update(db, user.id, category_id, data)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Categories"])
def delete_category(
    category_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Elimina una categoría. Los eventos vinculados quedan sin categoría."""
    category_service.delete(db, user.id, category_id)


# ══════════════════════════════════════════════════════════════════════════════
# REMINDERS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/reminders", response_model=list[ReminderResponse], tags=["Reminders"])
def list_reminders(
    reminder_status: Optional[ReminderStatus]   = Query(default=None, alias="status"),
    priority:        Optional[ReminderPriority] = Query(default=None),
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Lista recordatorios del usuario.
    Sin filtros devuelve todos. Filtrar por status=pending para el panel lateral.
    """
    return reminder_service.get_all(db, user.id, reminder_status, priority)


@router.post("/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED, tags=["Reminders"])
def create_reminder(
    data: ReminderCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Crea un recordatorio en estado pending."""
    return reminder_service.create(db, user.id, data)


@router.patch("/reminders/{reminder_id}", response_model=ReminderResponse, tags=["Reminders"])
def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Actualiza título, descripción, prioridad o fecha límite de un recordatorio."""
    return reminder_service.update(db, user.id, reminder_id, data)


@router.delete("/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Reminders"])
def delete_reminder(
    reminder_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Elimina un recordatorio y su evento vinculado si existe."""
    reminder_service.delete(db, user.id, reminder_id)


@router.post(
    "/reminders/{reminder_id}/schedule",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Reminders"],
)
def schedule_reminder(
    reminder_id: int,
    data: ReminderSchedule,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Asigna un recordatorio a una franja horaria.
    Crea un Event vinculado y marca el reminder como scheduled.
    Este es el endpoint que llama el frontend al hacer drag & drop.
    """
    return event_service.create_from_reminder(db, user.id, reminder_id, data)


# ══════════════════════════════════════════════════════════════════════════════
# EVENTS
# — Rutas estáticas ANTES que rutas con parámetros
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/events/today", response_model=list[EventResponse], tags=["Calendar"])
def list_events_today(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Devuelve todos los eventos del día actual en UTC."""
    return event_service.get_today(db, user.id)


@router.get("/events", response_model=list[EventResponse], tags=["Calendar"])
def list_events(
    start: datetime = Query(..., description="Inicio del rango en ISO 8601"),
    end:   datetime = Query(..., description="Fin del rango en ISO 8601"),
    db:    Session  = Depends(get_db),
    user:  User     = Depends(get_current_user),
):
    """
    Lista eventos reales en el rango dado.
    Las ocurrencias de rutinas se devuelven mezcladas mediante expand_in_range.
    """
    real_events    = event_service.get_range(db, user.id, start, end)
    routine_occs   = routine_service.expand_in_range(db, user.id, start, end)

    # Convertir ocurrencias de rutinas a dicts compatibles con EventResponse
    # Las ocurrencias virtuales se devuelven como objetos simples
    return real_events + [_routine_occ_to_response(occ) for occ in routine_occs]


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED, tags=["Calendar"])
def create_event(
    data: EventCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Crea un evento manual con opciones de DND y recordatorio."""
    return event_service.create(db, user.id, data)


@router.get("/events/{event_id}", response_model=EventResponse, tags=["Calendar"])
def get_event(
    event_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Obtiene un evento por ID."""
    return event_service.get_by_id(db, user.id, event_id)


@router.patch("/events/{event_id}", response_model=EventResponse, tags=["Calendar"])
def update_event(
    event_id: int,
    data: EventUpdate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Actualiza un evento. Acepta campos parciales.
    Si cambian start_at o reminder_minutes, se re-programa la notificación.
    """
    return event_service.update(db, user.id, event_id, data)


@router.patch(
    "/events/{event_id}/complete",
    response_model=EventResponse,
    tags=["Calendar"],
)
def complete_event(
    event_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Marca un evento como completado.
    Si tiene reminder vinculado, lo marca como done.
    """
    return event_service.complete(db, user.id, event_id)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Calendar"])
def delete_event(
    event_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Elimina un evento.
    Si tenía un reminder vinculado, lo devuelve a estado pending.
    """
    event_service.delete(db, user.id, event_id)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTINES
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/routines", response_model=list[RoutineResponse], tags=["Routines"])
def list_routines(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Lista todas las rutinas del usuario."""
    return routine_service.get_all(db, user.id)


@router.post("/routines", response_model=RoutineResponse, status_code=status.HTTP_201_CREATED, tags=["Routines"])
def create_routine(
    data: RoutineCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Crea una rutina recurrente. El campo rrule debe ser una RRULE RFC 5545 válida."""
    return routine_service.create(db, user.id, data)


@router.put("/routines/{routine_id}", response_model=RoutineResponse, tags=["Routines"])
def update_routine(
    routine_id: int,
    data: RoutineUpdate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Edita una rutina completa. Afecta a todas las instancias futuras
    que no tengan una excepción registrada.
    """
    return routine_service.update(db, user.id, routine_id, data)


@router.delete("/routines/{routine_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Routines"])
def delete_routine(
    routine_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Elimina una rutina y todas sus excepciones en cascada."""
    routine_service.delete(db, user.id, routine_id)


@router.post(
    "/routines/{routine_id}/exceptions",
    response_model=RoutineExceptionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Routines"],
)
def add_routine_exception(
    routine_id: int,
    data: RoutineExceptionCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Cancela o modifica una instancia concreta de una rutina.
    Solo afecta a esa ocurrencia — el resto no cambia.
    """
    return routine_service.add_exception(db, user.id, routine_id, data)


# ══════════════════════════════════════════════════════════════════════════════
# FCM TOKENS
# ══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/fcm-tokens",
    response_model=FcmTokenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Calendar"],
)
def register_fcm_token(
    data: FcmTokenCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Registra el token FCM del dispositivo al hacer login.
    Si el token ya existe, actualiza last_used_at.
    """
    from datetime import timezone
    existing = db.query(FcmToken).filter(FcmToken.token == data.token).first()
    if existing:
        from datetime import datetime
        existing.last_used_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    token = FcmToken(
        user_id=user.id,
        token=data.token,
        device_type=data.device_type,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


@router.delete("/fcm-tokens/{token}", status_code=status.HTTP_204_NO_CONTENT, tags=["Calendar"])
def delete_fcm_token(
    token: str,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Elimina el token FCM al hacer logout."""
    fcm = (
        db.query(FcmToken)
        .filter(FcmToken.token == token, FcmToken.user_id == user.id)
        .first()
    )
    if not fcm:
        raise FcmTokenNotFoundError(token)
    db.delete(fcm)
    db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# HELPER INTERNO
# ══════════════════════════════════════════════════════════════════════════════

def _routine_occ_to_response(occ: dict) -> EventResponse:
    """
    Convierte un dict de ocurrencia virtual de rutina a EventResponse.
    Las ocurrencias de rutina tienen id=None — el frontend las distingue
    por routine_id != None.
    """
    return EventResponse(
        id=occ["id"],
        user_id=occ["user_id"],
        routine_id=occ["routine_id"],
        reminder_id=occ["reminder_id"],
        category_id=occ["category_id"],
        title=occ["title"],
        description=occ["description"],
        start_at=occ["start_at"],
        end_at=occ["end_at"],
        all_day=occ["all_day"],
        color_override=occ["color_override"],
        enable_dnd=occ["enable_dnd"],
        reminder_minutes=occ["reminder_minutes"],
        google_event_id=occ["google_event_id"],
        apple_event_id=occ["apple_event_id"],
        is_cancelled=occ["is_cancelled"],
        created_at=occ["created_at"],
        updated_at=occ["updated_at"],
        category=occ["category"],
    )