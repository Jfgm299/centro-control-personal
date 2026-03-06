from datetime import date, datetime, time
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from dateutil.rrule import rruleset, rrulestr
from ..models.routine import Routine
from ..models.routine_exception import RoutineException
from ..calendar_schema import (
    RoutineCreate, RoutineUpdate,
    RoutineExceptionCreate, EventResponse,
)
from ..enums import RoutineExceptionAction
from ..exceptions import (
    RoutineNotFoundError,
    RoutineExceptionAlreadyExistsError,
    InvalidRoutineRangeError,
)


def _get_routine(db: Session, user_id: int, routine_id: int) -> Routine:
    routine = (
        db.query(Routine)
        .options(joinedload(Routine.category), joinedload(Routine.exceptions))
        .filter(Routine.id == routine_id, Routine.user_id == user_id)
        .first()
    )
    if not routine:
        raise RoutineNotFoundError(routine_id)
    return routine


def _expand_routine(routine: Routine, start: datetime, end: datetime) -> list[dict]:
    """
    Expande la RRULE de una rutina en ocurrencias concretas dentro del rango,
    aplicando las excepciones registradas.
    """
    try:
        base_rule = rrulestr(routine.rrule, dtstart=datetime.combine(routine.valid_from, routine.start_time))
    except Exception:
        return []

    ruleset = rruleset()
    ruleset.rrule(base_rule)

    # Índice de excepciones por fecha
    exceptions_by_date: dict[date, RoutineException] = {
        exc.original_date: exc for exc in routine.exceptions
    }

    # Aplicar cancelaciones como exdates
    for exc_date, exc in exceptions_by_date.items():
        if exc.action == RoutineExceptionAction.CANCELLED:
            exdate = datetime.combine(exc_date, routine.start_time)
            ruleset.exdate(exdate)

    # Respetar valid_until
    occurrences = []
    for dt in ruleset.between(start, end, inc=True):
        if routine.valid_until and dt.date() > routine.valid_until:
            break

        occ_date = dt.date()
        exc      = exceptions_by_date.get(occ_date)

        # Calcular start/end de esta ocurrencia
        if exc and exc.action == RoutineExceptionAction.MODIFIED and exc.new_start_at:
            occ_start = exc.new_start_at
            occ_end   = exc.new_end_at or datetime.combine(occ_date, routine.end_time)
        else:
            occ_start = dt
            occ_end   = datetime.combine(occ_date, routine.end_time)

        occurrences.append({
            "id":               None,          # instancias virtuales no tienen id de DB
            "user_id":          routine.user_id,
            "routine_id":       routine.id,
            "reminder_id":      None,
            "category_id":      routine.category_id,
            "title":            (exc.new_title if exc and exc.new_title else routine.title),
            "description":      routine.description,
            "start_at":         occ_start,
            "end_at":           occ_end,
            "all_day":          False,
            "color_override":   None,
            "enable_dnd":       (exc.new_enable_dnd if exc and exc.new_enable_dnd is not None
                                 else routine.enable_dnd),
            "reminder_minutes": (exc.new_reminder_minutes if exc and exc.new_reminder_minutes is not None
                                 else routine.reminder_minutes),
            "google_event_id":  None,
            "apple_event_id":   None,
            "is_cancelled":     False,
            "created_at":       datetime.combine(routine.valid_from, time()),
            "updated_at":       None,
            "category":         routine.category,
        })
    return occurrences


class RoutineService:

    def get_all(self, db: Session, user_id: int) -> list[Routine]:
        return (
            db.query(Routine)
            .options(joinedload(Routine.category))
            .filter(Routine.user_id == user_id)
            .order_by(Routine.title)
            .all()
        )

    def get_by_id(self, db: Session, user_id: int, routine_id: int) -> Routine:
        return _get_routine(db, user_id, routine_id)

    def create(self, db: Session, user_id: int, data: RoutineCreate) -> Routine:
        if data.valid_until and data.valid_until <= data.valid_from:
            raise InvalidRoutineRangeError()

        routine = Routine(
            user_id=user_id,
            category_id=data.category_id,
            title=data.title,
            description=data.description,
            rrule=data.rrule,
            start_time=data.start_time,
            end_time=data.end_time,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            enable_dnd=data.enable_dnd,
            reminder_minutes=data.reminder_minutes,
        )
        db.add(routine)
        db.commit()
        db.refresh(routine)
        return _get_routine(db, user_id, routine.id)

    def update(self, db: Session, user_id: int, routine_id: int, data: RoutineUpdate) -> Routine:
        routine = _get_routine(db, user_id, routine_id)

        update_data = data.model_dump(exclude_none=True)

        # Validar rango si se actualizan fechas
        valid_from  = update_data.get("valid_from",  routine.valid_from)
        valid_until = update_data.get("valid_until", routine.valid_until)
        if valid_until and valid_until <= valid_from:
            raise InvalidRoutineRangeError()

        for key, value in update_data.items():
            setattr(routine, key, value)

        db.commit()
        db.refresh(routine)
        return _get_routine(db, user_id, routine_id)

    def delete(self, db: Session, user_id: int, routine_id: int) -> None:
        routine = _get_routine(db, user_id, routine_id)
        db.delete(routine)
        db.commit()

    def add_exception(
        self,
        db: Session,
        user_id: int,
        routine_id: int,
        data: RoutineExceptionCreate,
    ) -> RoutineException:
        routine = _get_routine(db, user_id, routine_id)

        # No permitir dos excepciones para la misma fecha
        existing = (
            db.query(RoutineException)
            .filter(
                RoutineException.routine_id == routine_id,
                RoutineException.original_date == data.original_date,
            )
            .first()
        )
        if existing:
            raise RoutineExceptionAlreadyExistsError(routine_id, str(data.original_date))

        exception = RoutineException(
            routine_id=routine_id,
            original_date=data.original_date,
            action=data.action,
            new_start_at=data.new_start_at,
            new_end_at=data.new_end_at,
            new_title=data.new_title,
            new_enable_dnd=data.new_enable_dnd,
            new_reminder_minutes=data.new_reminder_minutes,
        )
        db.add(exception)
        db.commit()
        db.refresh(exception)
        return exception

    def expand_in_range(
        self,
        db: Session,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> list[dict]:
        """
        Devuelve todas las ocurrencias de rutinas activas del usuario en el rango.
        Se usa en el endpoint GET /calendar/events para combinar eventos reales + rutinas.
        """
        routines = (
            db.query(Routine)
            .options(joinedload(Routine.category), joinedload(Routine.exceptions))
            .filter(Routine.user_id == user_id, Routine.is_active == True)
            .all()
        )
        result = []
        for routine in routines:
            result.extend(_expand_routine(routine, start, end))
        return result