"""
Autenticación para Apple Calendar via CalDAV.

Apple no usa OAuth — usa Apple ID + app-specific password.
El usuario genera la app-specific password en appleid.apple.com.

IMPORTANTE: Las credenciales se encriptan en DB usando Fernet (ENCRYPTION_KEY).
"""
from cryptography.fernet import Fernet
from app.modules.calendar_tracker.manifest import get_settings


def get_fernet() -> Fernet:
    cfg = get_settings()
    return Fernet(cfg["ENCRYPTION_KEY"].strip().encode())


def encrypt(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return get_fernet().decrypt(value.encode()).decode()


def validate_credentials(username: str, password: str) -> bool:
    """
    Verifica que las credenciales CalDAV son válidas intentando conectar.
    Devuelve True si la conexión es exitosa.
    """
    from app.modules.calendar_tracker.integrations.apple.client import AppleCalendarClient
    try:
        client = AppleCalendarClient(username=username, password=password)
        client.list_calendars()
        return True
    except Exception:
        return False