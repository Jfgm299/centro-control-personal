"""
Clase base para proveedores de calendario externos.
Cada proveedor (Google, Apple) implementa esta interfaz.

EXTENSIÓN FUTURA — Recordatorios:
    Añadir métodos abstractos push_reminders() / pull_reminders()
    cuando se implemente Google Tasks / Apple Reminders (CalDAV VTODO).
"""
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session


class AbstractCalendarProvider(ABC):

    @abstractmethod
    def push_events(self, user_id: int, db: Session) -> dict:
        """Exporta eventos y rutinas de nuestra DB al calendario externo."""
        ...

    @abstractmethod
    def pull_events(self, user_id: int, db: Session) -> dict:
        """Importa eventos del calendario externo a nuestra DB."""
        ...

    @abstractmethod
    def validate_connection(self, user_id: int, db: Session) -> bool:
        """Verifica que la conexión sigue siendo válida."""
        ...