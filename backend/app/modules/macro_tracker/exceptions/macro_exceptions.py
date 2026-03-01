from app.core.exeptions import AppException


class ProductNotFoundInAPIError(AppException):
    def __init__(self, barcode: str):
        super().__init__(
            message=f"Producto con código de barras '{barcode}' no encontrado en Open Food Facts",
            status_code=404,
        )
        self.barcode = barcode


class ProductNotFoundError(AppException):
    def __init__(self, product_id: int):
        super().__init__(
            message=f"Producto {product_id} no encontrado",
            status_code=404,
        )
        self.product_id = product_id


class DiaryEntryNotFoundError(AppException):
    def __init__(self, entry_id: int):
        super().__init__(
            message=f"Entrada de diario {entry_id} no encontrada",
            status_code=404,
        )
        self.entry_id = entry_id


class OFFTimeoutError(AppException):
    def __init__(self):
        super().__init__(
            message="El servicio de datos de alimentos no está disponible. Inténtalo de nuevo.",
            status_code=503,
        )


class OFFRateLimitError(AppException):
    def __init__(self):
        super().__init__(
            message="Se ha alcanzado el límite de consultas a Open Food Facts. Inténtalo más tarde.",
            status_code=503,
        )


class OFFError(AppException):
    def __init__(self):
        super().__init__(
            message="Error inesperado del servicio de datos de alimentos.",
            status_code=503,
        )