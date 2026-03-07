"""
Cliente CalDAV para Apple Calendar.

Usa caldav library para comunicarse con iCloud CalDAV.
"""
from typing import Optional
import caldav
from app.modules.calendar_tracker.manifest import get_settings


APPLE_CALDAV_URL = "https://caldav.icloud.com"


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
        self._principal  = None
        self._calendar   = None

    def _get_principal(self) -> caldav.Principal:
        if not self._principal:
            self._principal = self._client.principal()
        return self._principal

    def _get_calendar(self) -> caldav.Calendar:
        if not self._calendar:
            principal = self._get_principal()
            calendars = principal.calendars()
            if self.calendar_id:
                match = next(
                    (c for c in calendars if str(c.url).endswith(self.calendar_id)),
                    None
                )
                self._calendar = match or calendars[0]
            else:
                self._calendar = calendars[0]
        return self._calendar

    def list_calendars(self) -> list[dict]:
        principal = self._get_principal()
        return [
            {"id": str(c.url).split("/")[-2], "name": c.name}
            for c in principal.calendars()
        ]

    def list_events(self, start, end) -> list:
        calendar = self._get_calendar()
        return calendar.date_search(start=start, end=end, expand=True)

    def create_event(self, ical_string: str) -> caldav.Event:
        calendar = self._get_calendar()
        return calendar.save_event(ical_string)

    def update_event(self, apple_event_id: str, ical_string: str) -> None:
        calendar = self._get_calendar()
        events   = calendar.events()
        for event in events:
            if apple_event_id in str(event.url):
                event.data = ical_string
                event.save()
                return

    def delete_event(self, apple_event_id: str) -> None:
        calendar = self._get_calendar()
        events   = calendar.events()
        for event in events:
            if apple_event_id in str(event.url):
                event.delete()
                return