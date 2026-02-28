from app.core.exeptions import AppException


class FlightNotFoundInAPIError(AppException):
    def __init__(self, flight_number: str, date: str):
        super().__init__(
            message=f"Vuelo {flight_number} no encontrado el {date}",
            status_code=404
        )
        self.flight_number = flight_number
        self.date = date


class FlightAlreadyExistsError(AppException):
    def __init__(self, flight_number: str, date: str):
        super().__init__(
            message=f"Ya tienes registrado el vuelo {flight_number} el {date}",
            status_code=409
        )
        self.flight_number = flight_number
        self.date = date


class FlightNotFoundError(AppException):
    def __init__(self, flight_id: int):
        super().__init__(
            message=f"Vuelo {flight_id} no encontrado",
            status_code=404
        )
        self.flight_id = flight_id


class AeroDataBoxTimeoutError(AppException):
    def __init__(self):
        super().__init__(
            message="El servicio de datos de vuelos no está disponible. Inténtalo de nuevo.",
            status_code=503
        )


class AeroDataBoxRateLimitError(AppException):
    def __init__(self):
        super().__init__(
            message="Se ha alcanzado el límite de consultas a la API de vuelos. Inténtalo más tarde.",
            status_code=503
        )


class AeroDataBoxError(AppException):
    def __init__(self):
        super().__init__(
            message="Error inesperado del servicio de datos de vuelos.",
            status_code=503
        )


class FlightRefreshThrottleError(AppException):
    def __init__(self):
        super().__init__(
            message="Refresh demasiado frecuente. Espera al menos 5 minutos entre actualizaciones.",
            status_code=429
        )