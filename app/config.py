"""Configuración de la aplicación e-paper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass
class GoogleConfig:
    credentials_file: Path
    token_file: Path
    calendar_id: str
    days_ahead: int
    max_unread_emails: int


@dataclass
class DisplayConfig:
    mock: bool
    mock_output: Path
    font_regular: Path
    font_bold: Path
    welcome_seconds: float


@dataclass
class ButtonsConfig:
    key1: int
    key2: int
    key3: int
    key4: int


@dataclass
class RefreshConfig:
    auto_interval_seconds: int


@dataclass
class AppConfig:
    google: GoogleConfig
    display: DisplayConfig
    buttons: ButtonsConfig
    refresh: RefreshConfig


def _resolve_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or ROOT_DIR / "config.yaml"
    if not config_path.exists():
        example = ROOT_DIR / "config.example.yaml"
        raise FileNotFoundError(
            f"No se encontró {config_path}. Copia {example.name} a config.yaml."
        )

    with config_path.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}

    google = raw.get("google", {})
    display = raw.get("display", {})
    buttons = raw.get("buttons", {})
    refresh = raw.get("refresh", {})

    return AppConfig(
        google=GoogleConfig(
            credentials_file=_resolve_path(
                google.get("credentials_file", "credentials/credentials.json")
            ),
            token_file=_resolve_path(google.get("token_file", "token.json")),
            calendar_id=google.get("calendar_id", "primary"),
            days_ahead=int(google.get("days_ahead", 14)),
            max_unread_emails=int(google.get("max_unread_emails", 5)),
        ),
        display=DisplayConfig(
            mock=bool(display.get("mock", False)),
            mock_output=_resolve_path(display.get("mock_output", "preview.png")),
            font_regular=Path(display.get(
                "font_regular",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            )),
            font_bold=Path(display.get(
                "font_bold",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            )),
            welcome_seconds=float(display.get("welcome_seconds", 2)),
        ),
        buttons=ButtonsConfig(
            key1=int(buttons.get("key1", 5)),
            key2=int(buttons.get("key2", 6)),
            key3=int(buttons.get("key3", 13)),
            key4=int(buttons.get("key4", 19)),
        ),
        refresh=RefreshConfig(
            auto_interval_seconds=int(refresh.get("auto_interval_seconds", 900)),
        ),
    )
