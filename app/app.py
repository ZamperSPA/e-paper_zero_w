"""Aplicación principal: estado, sincronización y acciones de botones."""

from __future__ import annotations

import logging
import threading
import time
from datetime import date, timedelta

from app.buttons import ButtonController
from app.config import AppConfig
from app.display import EpaperDisplay
from app.google_services import GoogleServices
from app.models import AppState, Screen
from app.screens import ScreenRenderer

logger = logging.getLogger(__name__)


class EpaperCalendarApp:
    SCREENS_ORDER = (
        Screen.CALENDAR_DAY,
        Screen.CALENDAR_AGENDA,
        Screen.NOTIFICATIONS,
    )

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.state = AppState()
        self._lock = threading.Lock()
        self._dirty = True
        self._running = False

        self.display = EpaperDisplay(config.display)
        self.renderer = ScreenRenderer(self.display)
        self.google = GoogleServices(config.google)
        self.buttons = ButtonController(config.buttons, self.handle_button)

    def run(self) -> None:
        self._running = True
        self.display.init()
        self.refresh_data()
        self._render_if_needed(force=True)

        auto_interval = self.config.refresh.auto_interval_seconds
        next_auto = time.monotonic() + auto_interval if auto_interval > 0 else None

        try:
            while self._running:
                self._render_if_needed()
                if next_auto and time.monotonic() >= next_auto:
                    self.refresh_data()
                    next_auto = time.monotonic() + auto_interval
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Deteniendo aplicación...")
        finally:
            self.display.sleep()

    def stop(self) -> None:
        self._running = False

    def handle_button(self, key: str) -> None:
        if key == "key3":
            self.refresh_data()
            return

        with self._lock:
            if key == "key1":
                self._on_key1()
            elif key == "key2":
                self._on_key2()
            elif key == "key4":
                self._on_key4()
            self._dirty = True

    def refresh_data(self) -> None:
        logger.info("Sincronizando con Google...")
        data = self.google.fetch_data()
        with self._lock:
            self.state.data = data
            self._dirty = True
        logger.info("Sincronización completada")

    def _on_key1(self) -> None:
        if self.state.screen == Screen.CALENDAR_DAY:
            self.state.selected_day -= timedelta(days=1)
        elif self.state.screen == Screen.NOTIFICATIONS:
            self.state.screen = Screen.CALENDAR_DAY
        else:
            self.state.screen = Screen.CALENDAR_DAY

    def _on_key2(self) -> None:
        if self.state.screen == Screen.CALENDAR_DAY:
            self.state.selected_day += timedelta(days=1)
        else:
            self._cycle_screen(forward=True)

    def _on_key4(self) -> None:
        if self.state.screen == Screen.CALENDAR_DAY:
            self.state.screen = Screen.CALENDAR_AGENDA
        elif self.state.screen == Screen.CALENDAR_AGENDA:
            self.state.screen = Screen.NOTIFICATIONS
        else:
            self.state.screen = Screen.CALENDAR_DAY
            self.state.selected_day = date.today()

    def _cycle_screen(self, forward: bool = True) -> None:
        order = self.SCREENS_ORDER
        index = order.index(self.state.screen)
        index = (index + 1) % len(order) if forward else (index - 1) % len(order)
        self.state.screen = order[index]

    def _render_if_needed(self, force: bool = False) -> None:
        with self._lock:
            if not force and not self._dirty:
                return
            self._dirty = False
            state_snapshot = AppState(
                screen=self.state.screen,
                selected_day=self.state.selected_day,
                data=self.state.data,
            )

        self.renderer.render(state_snapshot)
