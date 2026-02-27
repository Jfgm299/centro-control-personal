from fastapi.responses import JSONResponse
from app.core.exeptions import AppException, NotYoursError

# Handler genérico para cualquier AppException
async def app_exception_handler(request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

async def not_yours_handler(request, exc: NotYoursError):
    return JSONResponse(
        status_code=403,
        content={"detail": exc.message}
    )

CORE_EXCEPTION_HANDLERS = {
    AppException: app_exception_handler,
    NotYoursError: not_yours_handler,
}