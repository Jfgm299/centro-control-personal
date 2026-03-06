# app/modules/automations_engine/__init__.py
from fastapi import APIRouter
from .routers.automations_router import router as automations_router
from .routers.executions_router import router as executions_router
from .routers.webhooks_router import router as webhooks_router
from .routers.api_keys_router import router as api_keys_router
from .routers.registry_router import router as registry_router
from .handlers import register_exception_handlers as register_handlers

router = APIRouter()
router.include_router(automations_router)
router.include_router(executions_router)
router.include_router(webhooks_router)
router.include_router(api_keys_router)
router.include_router(registry_router)

TAGS = [
    {"name": "Automations", "description": "Gestión de automatizaciones y flujos"},
    {"name": "Executions",  "description": "Historial de ejecuciones"},
    {"name": "Webhooks",    "description": "Webhooks entrantes"},
    {"name": "API Keys",    "description": "Gestión de API keys"},
    {"name": "Registry",    "description": "Triggers y acciones disponibles"},
]
TAG_GROUP = {
    "name": "Automations Engine",
    "tags": ["Automations", "Executions", "Webhooks", "API Keys", "Registry"]
}

__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP"]