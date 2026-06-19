#!/usr/bin/env python3
"""
Calendario e-paper para Waveshare 2.7\" HAT (B) + cuenta Gmail.

Requisitos en Raspberry Pi:
  1. Habilitar SPI: sudo raspi-config -> Interface Options -> SPI
  2. Instalar dependencias del sistema:
       sudo apt install python3-pip python3-pil python3-numpy python3-gpiozero
  3. Instalar drivers Waveshare:
       git clone https://github.com/waveshare/e-Paper.git
       cd e-Paper/RaspberryPi_JetsonNano/python && pip install .
  4. pip install -r requirements.txt
  5. Copiar config.example.yaml -> config.yaml
  6. Colocar credentials.json en credentials/ (Google Cloud OAuth)
  7. Primera ejecución: python main.py (autenticación por consola)
"""

from __future__ import annotations

import argparse
import logging
import sys

from app.app import EpaperCalendarApp
from app.config import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calendario e-paper Gmail")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Simular pantalla (guarda preview.png, sin hardware)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Logs detallados",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        config = load_config()
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1

    if args.mock:
        config.display.mock = True

    app = EpaperCalendarApp(config)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
