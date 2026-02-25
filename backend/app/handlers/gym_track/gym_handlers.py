from fastapi import Request
from fastapi.responses import JSONResponse
from ...exceptions import WorkoutAlreadyEndedError, WorkoutNotFound, WorkoutAlreadyActiveError

async def workout_already_ended_handler(request: Request, exc: WorkoutAlreadyEndedError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

async def workout_not_found_handler(request: Request, exc: WorkoutNotFound):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail":exc.message}
    )

async def workout_already_active_handler(request: Request, exc: WorkoutAlreadyActiveError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail":exc.message}
    )

#Dicctionary to help register
GYM_EXCEPTION_HANDLERS = {
    WorkoutAlreadyEndedError: workout_already_ended_handler,
    WorkoutNotFound: workout_not_found_handler,
    WorkoutAlreadyActiveError: workout_already_active_handler,
}