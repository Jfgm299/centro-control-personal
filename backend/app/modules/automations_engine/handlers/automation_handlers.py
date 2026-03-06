from fastapi import Request
from fastapi.responses import JSONResponse
from ..exceptions import (
    AutomationNotFoundError,
    AutomationNameAlreadyExistsError,
    InvalidFlowError,
    ExecutionNotFoundError,
    ApiKeyNotFoundError,
    ApiKeyInvalidError,
    ApiKeyExpiredError,
    ApiKeyInsufficientScopeError,
    WebhookNotFoundError,
    WebhookTokenInvalidError,
    FlowDepthExceededError,
    TriggerNotFoundInRegistryError,
    ActionNotFoundInRegistryError,
)


async def automation_not_found_handler(request: Request, exc: AutomationNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def automation_name_already_exists_handler(request: Request, exc: AutomationNameAlreadyExistsError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def invalid_flow_handler(request: Request, exc: InvalidFlowError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def execution_not_found_handler(request: Request, exc: ExecutionNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def api_key_not_found_handler(request: Request, exc: ApiKeyNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def api_key_invalid_handler(request: Request, exc: ApiKeyInvalidError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def api_key_expired_handler(request: Request, exc: ApiKeyExpiredError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def api_key_insufficient_scope_handler(request: Request, exc: ApiKeyInsufficientScopeError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def webhook_not_found_handler(request: Request, exc: WebhookNotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def webhook_token_invalid_handler(request: Request, exc: WebhookTokenInvalidError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def flow_depth_exceeded_handler(request: Request, exc: FlowDepthExceededError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def trigger_not_found_in_registry_handler(request: Request, exc: TriggerNotFoundInRegistryError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


async def action_not_found_in_registry_handler(request: Request, exc: ActionNotFoundInRegistryError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


AUTOMATION_EXCEPTION_HANDLERS = {
    AutomationNotFoundError:           automation_not_found_handler,
    AutomationNameAlreadyExistsError:  automation_name_already_exists_handler,
    InvalidFlowError:                  invalid_flow_handler,
    ExecutionNotFoundError:            execution_not_found_handler,
    ApiKeyNotFoundError:               api_key_not_found_handler,
    ApiKeyInvalidError:                api_key_invalid_handler,
    ApiKeyExpiredError:                api_key_expired_handler,
    ApiKeyInsufficientScopeError:      api_key_insufficient_scope_handler,
    WebhookNotFoundError:              webhook_not_found_handler,
    WebhookTokenInvalidError:          webhook_token_invalid_handler,
    FlowDepthExceededError:            flow_depth_exceeded_handler,
    TriggerNotFoundInRegistryError:    trigger_not_found_in_registry_handler,
    ActionNotFoundInRegistryError:     action_not_found_in_registry_handler,
}