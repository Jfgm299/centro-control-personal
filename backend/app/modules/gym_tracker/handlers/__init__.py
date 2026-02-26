from .gym_track.gym_handlers import GYM_EXCEPTION_HANDLERS

def register_exception_handlers(app):
    """Registra todos los exception handlers de la aplicación"""
    for exc_class, handler in GYM_EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)