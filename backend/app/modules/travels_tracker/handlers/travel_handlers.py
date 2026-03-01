from fastapi import Request
from fastapi.responses import JSONResponse
from ..exceptions.travel_exceptions import (
    TripNotFoundError,
    AlbumNotFoundError,
    PhotoNotFoundError,
    ActivityNotFoundError,
    PhotoAlreadyConfirmedError,
    PhotoNotUploadedToStorageError,
    InvalidContentTypeError,
    TripPhotoLimitReachedError,
    StorageError,
)


async def trip_not_found_handler(request: Request, exc: TripNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def album_not_found_handler(request: Request, exc: AlbumNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def photo_not_found_handler(request: Request, exc: PhotoNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def activity_not_found_handler(request: Request, exc: ActivityNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def photo_already_confirmed_handler(request: Request, exc: PhotoAlreadyConfirmedError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def photo_not_uploaded_handler(request: Request, exc: PhotoNotUploadedToStorageError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def invalid_content_type_handler(request: Request, exc: InvalidContentTypeError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def trip_photo_limit_handler(request: Request, exc: TripPhotoLimitReachedError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def storage_error_handler(request: Request, exc: StorageError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


TRAVELS_EXCEPTION_HANDLERS = {
    TripNotFoundError:              trip_not_found_handler,
    AlbumNotFoundError:             album_not_found_handler,
    PhotoNotFoundError:             photo_not_found_handler,
    ActivityNotFoundError:          activity_not_found_handler,
    PhotoAlreadyConfirmedError:     photo_already_confirmed_handler,
    PhotoNotUploadedToStorageError: photo_not_uploaded_handler,
    InvalidContentTypeError:        invalid_content_type_handler,
    TripPhotoLimitReachedError:     trip_photo_limit_handler,
    StorageError:                   storage_error_handler,
}