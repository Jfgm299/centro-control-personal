"""
Cliente CalDAV para Apple Calendar.

Usa caldav library para comunicarse con iCloud CalDAV.

Selección de calendario (por orden de prioridad):
  1. calendar_id explícito (configurado por el usuario)
  2. Primer calendario editable con nombre estándar: Home, Calendar, Calendario, Personal
  3. Primer calendario editable (no suscrito, no read-only)
  4. Cualquier calendario disponible (fallback)
"""
from typing import Optional
import caldav
from app.modules.calendar_tracker.manifest import get_settings


APPLE_CALDAV_URL = "https://caldav.icloud.com"

# Nombres de calendario por defecto de iCloud en distintos idiomas
DEFAULT_CALENDAR_NAMES = {"home", "calendar", "calendario", "personal", "icloud"}


class AppleCalendarClient:

    def __init__(self, username: str, password: str, calendar_id: Optional[str] = None):
        self.username    = username
        self.password    = password
        self.calendar_id = calendar_id
        self._client     = caldav.DAVClient(
            url=APPLE_CALDAV_URL,
            username=username,
            password=password,
        )
        self._principal = None
        self._calendar  = None

    def _get_principal(self) -> caldav.Principal:
        if not self._principal:
            self._principal = self._client.principal()
        return self._principal

    def _is_writable(self, calendar: caldav.Calendar) -> bool:
        """Detecta si un calendario es editable (no suscrito, no read-only)."""
        try:
            props = calendar.get_properties([caldav.dav.ResourceType()])
            # Los calendarios suscritos suelen tener resourcetype subscribed o schedule-inbox
            rt = str(props.get("{DAV:}resourcetype", "")).lower()
            if "subscribed" in rt or "schedule-inbox" in rt or "schedule-outbox" in rt:
                return False
        except Exception:
            pass

        # Intentar verificar si tiene privilegio write
        try:
            privs = calendar.get_properties([caldav.dav.CurrentUserPrivilegeSet()])
            priv_str = str(privs.get("{DAV:}current-user-privilege-set", "")).lower()
            if priv_str and "write" not in priv_str:
                return False
        except Exception:
            pass

        return True

    def _get_calendar(self) -> caldav.Calendar:
        if self._calendar:
            return self._calendar

        principal  = self._get_principal()
        calendars  = principal.calendars()

        if not calendars:
            raise RuntimeError("No se encontraron calendarios en la cuenta de Apple")

        # 1. calendar_id explícito
        if self.calendar_id:
            match = next(
                (c for c in calendars if self.calendar_id in str(c.url)),
                None
            )
            if match:
                self._calendar = match
                return self._calendar

        # 2. Calendario editable con nombre estándar
        for cal in calendars:
            name = (cal.name or "").strip().lower()
            if name in DEFAULT_CALENDAR_NAMES and self._is_writable(cal):
                self._calendar = cal
                return self._calendar

        # 3. Primer calendario editable (el que no sea suscrito/read-only)
        for cal in calendars:
            if self._is_writable(cal):
                self._calendar = cal
                return self._calendar

        # 4. Fallback: cualquier calendario
        self._calendar = calendars[0]
        return self._calendar

    def list_calendars(self) -> list[dict]:
        """Lista los calendarios disponibles con nombre, id y si son editables."""
        principal = self._get_principal()
        result = []
        for c in principal.calendars():
            cal_id = str(c.url).rstrip("/").split("/")[-1]
            result.append({
                "id":       cal_id,
                "name":     c.name or cal_id,
                "writable": self._is_writable(c),
            })
        return result

    def list_events(self, start, end) -> list:
        calendar = self._get_calendar()
        return calendar.date_search(start=start, end=end, expand=True)

    def create_event(self, ical_string: str) -> caldav.Event:
        calendar = self._get_calendar()
        return calendar.save_event(ical_string)

    def update_event(self, apple_event_id: str, ical_string: str) -> None:
        calendar = self._get_calendar()
        for event in calendar.events():
            if apple_event_id in str(event.url):
                event.data = ical_string
                event.save()
                return

    def delete_event(self, apple_event_id: str) -> None:
        calendar = self._get_calendar()
        for event in calendar.events():
            if apple_event_id in str(event.url):
                event.delete()
                return