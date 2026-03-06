from app.core.exeptions import AppException


class EventNotFoundError(AppException):
    def __init__(self, event_id: int):
        super().__init__(
            message=f"Evento {event_id} no encontrado",
            status_code=404,
        )
        self.event_id = event_id


class ReminderNotFoundError(AppException):
    def __init__(self, reminder_id: int):
        super().__init__(
            message=f"Recordatorio {reminder_id} no encontrado",
            status_code=404,
        )
        self.reminder_id = reminder_id


class ReminderAlreadyScheduledError(AppException):
    def __init__(self, reminder_id: int):
        super().__init__(
            message=f"El recordatorio {reminder_id} ya tiene un evento asignado",
            status_code=409,
        )
        self.reminder_id = reminder_id


class ReminderNotScheduledError(AppException):
    def __init__(self, reminder_id: int):
        super().__init__(
            message=f"El recordatorio {reminder_id} no tiene un evento asignado",
            status_code=409,
        )
        self.reminder_id = reminder_id


class RoutineNotFoundError(AppException):
    def __init__(self, routine_id: int):
        super().__init__(
            message=f"Rutina {routine_id} no encontrada",
            status_code=404,
        )
        self.routine_id = routine_id


class RoutineExceptionNotFoundError(AppException):
    def __init__(self, exception_id: int):
        super().__init__(
            message=f"Excepcion de rutina {exception_id} no encontrada",
            status_code=404,
        )
        self.exception_id = exception_id


class RoutineExceptionAlreadyExistsError(AppException):
    def __init__(self, routine_id: int, original_date: str):
        super().__init__(
            message=f"Ya existe una excepcion para la rutina {routine_id} en la fecha {original_date}",
            status_code=409,
        )
        self.routine_id    = routine_id
        self.original_date = original_date


class CategoryNotFoundError(AppException):
    def __init__(self, category_id: int):
        super().__init__(
            message=f"Categoria {category_id} no encontrada",
            status_code=404,
        )
        self.category_id = category_id


class CategoryNameAlreadyExistsError(AppException):
    def __init__(self, name: str):
        super().__init__(
            message=f"Ya existe una categoria con el nombre '{name}'",
            status_code=409,
        )
        self.name = name


class InvalidEventRangeError(AppException):
    def __init__(self):
        super().__init__(
            message="La fecha de inicio debe ser anterior a la fecha de fin",
            status_code=422,
        )


class InvalidRoutineRangeError(AppException):
    def __init__(self):
        super().__init__(
            message="valid_from debe ser anterior a valid_until",
            status_code=422,
        )


class FcmTokenNotFoundError(AppException):
    def __init__(self, token: str):
        super().__init__(
            message=f"Token FCM no encontrado",
            status_code=404,
        )
        self.token = token