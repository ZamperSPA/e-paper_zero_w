"""Modelos de datos compartidos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum, auto


class Screen(Enum):
    CALENDAR_DAY = auto()
    CALENDAR_AGENDA = auto()
    NOTIFICATIONS = auto()


@dataclass
class CalendarEvent:
    summary: str
    start: datetime
    end: datetime
    all_day: bool
    location: str = ""


@dataclass
class EmailNotification:
    sender: str
    subject: str
    received_at: datetime


@dataclass
class AppData:
    events: list[CalendarEvent] = field(default_factory=list)
    unread_emails: list[EmailNotification] = field(default_factory=list)
    unread_count: int = 0
    last_sync: datetime | None = None
    sync_error: str | None = None


@dataclass
class AppState:
    screen: Screen = Screen.CALENDAR_DAY
    selected_day: date = field(default_factory=date.today)
    data: AppData = field(default_factory=AppData)

    def events_for_day(self, day: date) -> list[CalendarEvent]:
        return [
            event
            for event in self.data.events
            if event.start.date() == day
        ]

    def upcoming_events(self, limit: int = 8) -> list[CalendarEvent]:
        now = datetime.now().astimezone()
        upcoming = [event for event in self.data.events if event.end >= now]
        return sorted(upcoming, key=lambda item: item.start)[:limit]
