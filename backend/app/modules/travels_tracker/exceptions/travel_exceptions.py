from app.core.exeptions import AppException


class TripNotFoundError(AppException):
    def __init__(self, trip_id: int):
        super().__init__(message=f"Viaje {trip_id} no encontrado", status_code=404)
        self.trip_id = trip_id


class AlbumNotFoundError(AppException):
    def __init__(self, album_id: int):
        super().__init__(message=f"Álbum {album_id} no encontrado", status_code=404)
        self.album_id = album_id


class PhotoNotFoundError(AppException):
    def __init__(self, photo_id: int):
        super().__init__(message=f"Foto {photo_id} no encontrada", status_code=404)
        self.photo_id = photo_id


class ActivityNotFoundError(AppException):
    def __init__(self, activity_id: int):
        super().__init__(message=f"Actividad {activity_id} no encontrada", status_code=404)
        self.activity_id = activity_id


class PhotoAlreadyConfirmedError(AppException):
    def __init__(self, photo_id: int):
        super().__init__(
            message=f"La foto {photo_id} ya fue confirmada anteriormente",
            status_code=409,
        )
        self.photo_id = photo_id


class PhotoNotUploadedToStorageError(AppException):
    def __init__(self, photo_id: int):
        super().__init__(
            message=(
                f"La foto {photo_id} no se encontró en el almacenamiento. "
                "¿Se completó el upload correctamente?"
            ),
            status_code=400,
        )
        self.photo_id = photo_id


class InvalidContentTypeError(AppException):
    def __init__(self, content_type: str):
        super().__init__(
            message=(
                f"Tipo de archivo '{content_type}' no permitido. "
                "Solo se aceptan imágenes (jpeg, png, webp, heic, gif)."
            ),
            status_code=422,
        )
        self.content_type = content_type


class TripPhotoLimitReachedError(AppException):
    def __init__(self, trip_id: int, limit: int):
        super().__init__(
            message=f"Has alcanzado el límite de {limit} fotos por viaje.",
            status_code=422,
        )
        self.trip_id = trip_id
        self.limit = limit


class StorageError(AppException):
    def __init__(self, detail: str = ""):
        super().__init__(
            message="Error en el servicio de almacenamiento. Inténtalo de nuevo.",
            status_code=503,
        )
        self.detail = detail