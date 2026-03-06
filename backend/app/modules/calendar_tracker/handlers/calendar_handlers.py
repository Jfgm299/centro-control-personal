from fastapi import Request
from fastapi.responses import JSONResponse
from ..exceptions import (
    EventNotFoundError,
    ReminderNotFoundError,
    ReminderAlreadyScheduledError,
    ReminderNotScheduledError,
    RoutineNotFoundError,
    RoutineExceptionNotFoundError,
    RoutineExceptionAlreadyExistsError,
    CategoryNotFoundError,
    CategoryNameAlreadyExistsError,
    InvalidEventRangeError,
    InvalidRoutineRangeError,
    FcmTokenNotFoundError,
)


async def event_not_found_handler(request: Request, exc: EventNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def reminder_not_found_handler(request: Request, exc: ReminderNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def reminder_already_scheduled_handler(request: Request, exc: ReminderAlreadyScheduledError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def reminder_not_scheduled_handler(request: Request, exc: ReminderNotScheduledError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def routine_not_found_handler(request: Request, exc: RoutineNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def routine_exception_not_found_handler(request: Request, exc: RoutineExceptionNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def routine_exception_already_exists_handler(request: Request, exc: RoutineExceptionAlreadyExistsError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def category_not_found_handler(request: Request, exc: CategoryNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def category_name_already_exists_handler(request: Request, exc: CategoryNameAlreadyExistsError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def invalid_event_range_handler(request: Request, exc: InvalidEventRangeError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def invalid_routine_range_handler(request: Request, exc: InvalidRoutineRangeError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def fcm_token_not_found_handler(request: Request, exc: FcmTokenNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


CALENDAR_EXCEPTION_HANDLERS = {
    EventNotFoundError:                    event_not_found_handler,
    ReminderNotFoundError:                 reminder_not_found_handler,
    ReminderAlreadyScheduledError:         reminder_already_scheduled_handler,
    ReminderNotScheduledError:             reminder_not_scheduled_handler,
    RoutineNotFoundError:                  routine_not_found_handler,
    RoutineExceptionNotFoundError:         routine_exception_not_found_handler,
    RoutineExceptionAlreadyExistsError:    routine_exception_already_exists_handler,
    CategoryNotFoundError:                 category_not_found_handler,
    CategoryNameAlreadyExistsError:        category_name_already_exists_handler,
    InvalidEventRangeError:                invalid_event_range_handler,
    InvalidRoutineRangeError:              invalid_routine_range_handler,
    FcmTokenNotFoundError:                 fcm_token_not_found_handler,
}