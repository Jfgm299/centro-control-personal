from app.core.exeptions import AppException


class AutomationNotFoundError(AppException):
    def __init__(self, automation_id: int):
        super().__init__(
            message=f"Automatización {automation_id} no encontrada",
            status_code=404,
        )
        self.automation_id = automation_id


class AutomationNameAlreadyExistsError(AppException):
    def __init__(self, name: str):
        super().__init__(
            message=f"Ya existe una automatización con el nombre '{name}'",
            status_code=409,
        )
        self.name = name


class InvalidFlowError(AppException):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Flujo inválido: {reason}",
            status_code=422,
        )
        self.reason = reason


class ExecutionNotFoundError(AppException):
    def __init__(self, execution_id: int):
        super().__init__(
            message=f"Ejecución {execution_id} no encontrada",
            status_code=404,
        )
        self.execution_id = execution_id


class ApiKeyNotFoundError(AppException):
    def __init__(self, key_id: int):
        super().__init__(
            message=f"API key {key_id} no encontrada",
            status_code=404,
        )
        self.key_id = key_id


class ApiKeyInvalidError(AppException):
    def __init__(self):
        super().__init__(
            message="API key inválida o revocada",
            status_code=401,
        )


class ApiKeyExpiredError(AppException):
    def __init__(self):
        super().__init__(
            message="API key expirada",
            status_code=401,
        )


class ApiKeyInsufficientScopeError(AppException):
    def __init__(self, required_scope: str):
        super().__init__(
            message=f"La API key no tiene el scope requerido: {required_scope}",
            status_code=403,
        )
        self.required_scope = required_scope


class WebhookNotFoundError(AppException):
    def __init__(self, webhook_id: int):
        super().__init__(
            message=f"Webhook {webhook_id} no encontrado",
            status_code=404,
        )
        self.webhook_id = webhook_id


class WebhookTokenInvalidError(AppException):
    def __init__(self):
        super().__init__(
            message="Token de webhook inválido o inactivo",
            status_code=404,
        )


class FlowDepthExceededError(AppException):
    def __init__(self, max_depth: int):
        super().__init__(
            message=f"Se ha superado la profundidad máxima de flujo ({max_depth} niveles)",
            status_code=422,
        )
        self.max_depth = max_depth


class TriggerNotFoundInRegistryError(AppException):
    def __init__(self, ref_id: str):
        super().__init__(
            message=f"Trigger '{ref_id}' no está registrado en ningún módulo instalado",
            status_code=422,
        )
        self.ref_id = ref_id


class ActionNotFoundInRegistryError(AppException):
    def __init__(self, ref_id: str):
        super().__init__(
            message=f"Acción '{ref_id}' no está registrada en ningún módulo instalado",
            status_code=422,
        )
        self.ref_id = ref_id