"""Filtros de eventos del calendario."""

from __future__ import annotations

from typing import Protocol

DEFAULT_HIDDEN_EVENTS = (
    "Casa",
    "Oficina",
    "Todo el dia Casa",
    "Todo el dia Oficina",
    "Todo el día Casa",
    "Todo el día Oficina",
)


class _HasSummary(Protocol):
    summary: str


def _normalize(text: str) -> str:
    lowered = text.strip().lower()
    for src, dst in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        lowered = lowered.replace(src, dst)
    return lowered


def is_hidden_event(event: _HasSummary, hidden: tuple[str, ...]) -> bool:
    summary = _normalize(event.summary)
    candidates = {summary, _normalize(f"Todo el dia {event.summary}")}

    for pattern in hidden:
        if _normalize(pattern) in candidates:
            return True

    return False


def filter_events(events: list[_HasSummary], hidden: tuple[str, ...]) -> list[_HasSummary]:
    if not hidden:
        return events
    return [event for event in events if not is_hidden_event(event, hidden)]
