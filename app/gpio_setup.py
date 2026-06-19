"""Configura gpiozero para Raspberry Pi OS moderno (Bookworm+)."""

from __future__ import annotations

import os
import sys


def configure_gpio() -> None:
    """Debe llamarse antes de importar gpiozero o waveshare_epd."""
    if sys.platform != "linux":
        return

    if os.environ.get("GPIOZERO_PIN_FACTORY"):
        return

    try:
        import lgpio  # noqa: F401
    except ImportError:
        return

    os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"
