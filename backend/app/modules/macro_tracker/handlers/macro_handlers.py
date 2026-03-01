from fastapi import Request
from fastapi.responses import JSONResponse
from ..exceptions import (
    ProductNotFoundInAPIError,
    ProductNotFoundError,
    DiaryEntryNotFoundError,
    OFFTimeoutError,
    OFFRateLimitError,
    OFFError,
)


async def product_not_found_in_api_handler(request: Request, exc: ProductNotFoundInAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def product_not_found_handler(request: Request, exc: ProductNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def diary_entry_not_found_handler(request: Request, exc: DiaryEntryNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def off_timeout_handler(request: Request, exc: OFFTimeoutError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def off_rate_limit_handler(request: Request, exc: OFFRateLimitError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def off_error_handler(request: Request, exc: OFFError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


MACRO_EXCEPTION_HANDLERS = {
    ProductNotFoundInAPIError: product_not_found_in_api_handler,
    ProductNotFoundError:      product_not_found_handler,
    DiaryEntryNotFoundError:   diary_entry_not_found_handler,
    OFFTimeoutError:           off_timeout_handler,
    OFFRateLimitError:         off_rate_limit_handler,
    OFFError:                  off_error_handler,
}