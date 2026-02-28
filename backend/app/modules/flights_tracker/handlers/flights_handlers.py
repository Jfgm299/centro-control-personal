from fastapi import Request
from fastapi.responses import JSONResponse
from ..exceptions import (
    FlightNotFoundInAPIError,
    FlightAlreadyExistsError,
    FlightNotFoundError,
    AeroDataBoxTimeoutError,
    AeroDataBoxRateLimitError,
    AeroDataBoxError,
    FlightRefreshThrottleError,
)


async def flight_not_found_in_api_handler(request: Request, exc: FlightNotFoundInAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def flight_already_exists_handler(request: Request, exc: FlightAlreadyExistsError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def flight_not_found_handler(request: Request, exc: FlightNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def aerodatabox_timeout_handler(request: Request, exc: AeroDataBoxTimeoutError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def aerodatabox_rate_limit_handler(request: Request, exc: AeroDataBoxRateLimitError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def aerodatabox_error_handler(request: Request, exc: AeroDataBoxError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def flight_refresh_throttle_handler(request: Request, exc: FlightRefreshThrottleError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


FLIGHTS_EXCEPTION_HANDLERS = {
    FlightNotFoundInAPIError:    flight_not_found_in_api_handler,
    FlightAlreadyExistsError:    flight_already_exists_handler,
    FlightNotFoundError:         flight_not_found_handler,
    AeroDataBoxTimeoutError:     aerodatabox_timeout_handler,
    AeroDataBoxRateLimitError:   aerodatabox_rate_limit_handler,
    AeroDataBoxError:            aerodatabox_error_handler,
    FlightRefreshThrottleError:  flight_refresh_throttle_handler,
}