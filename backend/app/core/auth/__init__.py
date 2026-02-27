from app.core.auth.user_router import router

TAGS = [
    {"name": "Auth", "description": "Registro, login y autenticación"},
]

TAG_GROUP = {
    "name": "Auth",
    "tags": ["Auth"]
}

__all__ = ['router', 'TAGS', 'TAG_GROUP']