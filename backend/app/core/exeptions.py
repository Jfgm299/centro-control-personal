class AppException(Exception):
    """Excepción base de la aplicación"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotYoursError(AppException):
    """El recurso existe pero no pertenece al usuario autenticado"""
    def __init__(self, resource: str = "recurso"):
        super().__init__(
            message=f"No tienes permiso para acceder a este {resource}",
            status_code=403
        )