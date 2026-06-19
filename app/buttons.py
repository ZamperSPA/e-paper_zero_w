"""Manejo de botones físicos del HAT."""

from __future__ import annotations

import logging
import sys
from typing import Callable

from app.config import ButtonsConfig

logger = logging.getLogger(__name__)


class ButtonController:
    def __init__(self, config: ButtonsConfig, on_press: Callable[[str], None]) -> None:
        self._on_press = on_press
        self._buttons = []
        self._mock = sys.platform != "linux"

        if self._mock:
            logger.warning("Botones en modo simulación (no es Linux/Raspberry Pi)")
            return

        from gpiozero import Button

        mapping = {
            "key1": config.key1,
            "key2": config.key2,
            "key3": config.key3,
            "key4": config.key4,
        }
        for name, pin in mapping.items():
            button = Button(pin, bounce_time=0.15)
            button.when_pressed = self._make_handler(name)
            self._buttons.append(button)
            logger.info("Botón %s registrado en GPIO %s", name, pin)

    def _make_handler(self, name: str):
        def handler() -> None:
            logger.debug("Botón presionado: %s", name)
            self._on_press(name)

        return handler

    def simulate_press(self, name: str) -> None:
        """Útil para pruebas en PC."""
        self._on_press(name)
