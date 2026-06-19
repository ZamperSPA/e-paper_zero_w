"""Autenticación y APIs de Google Calendar / Gmail."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import GoogleConfig
from app.models import AppData, CalendarEvent, EmailNotification

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]


class GoogleServices:
    def __init__(self, config: GoogleConfig) -> None:
        self.config = config
        self._credentials = self._load_credentials()
        self.calendar = build("calendar", "v3", credentials=self._credentials)
        self.gmail = build("gmail", "v1", credentials=self._credentials)

    def _load_credentials(self) -> Credentials:
        token_path = self.config.token_file
        creds: Credentials | None = None

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if creds and creds.valid:
            return creds

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
            return creds

        credentials_path = self.config.credentials_file
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Falta {credentials_path}. Descarga las credenciales OAuth desde "
                "Google Cloud Console (tipo 'Aplicación de escritorio')."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = self._authenticate(flow)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    def _authenticate(self, flow: InstalledAppFlow) -> Credentials:
        """OAuth para Pi sin navegador usando loopback (127.0.0.1), método soportado por Google."""
        print("\n=== Autorización Google (solo la primera vez) ===")
        print("Se abrirá un servidor local en la Pi para completar el login.\n")

        try:
            creds = flow.run_local_server(
                host="127.0.0.1",
                port=0,
                open_browser=False,
                authorization_prompt_message=(
                    "Abre esta URL en un teléfono o PC (misma cuenta Gmail):\n{url}"
                ),
                success_message=(
                    "Autorización recibida. Puedes volver a la terminal de la Pi."
                ),
            )
            return creds
        except OSError as exc:
            raise RuntimeError(
                "No se pudo iniciar el servidor OAuth local en la Pi. "
                f"Detalle: {exc}"
            ) from exc

    def fetch_data(self) -> AppData:
        data = AppData(last_sync=datetime.now().astimezone())
        try:
            data.events = self._fetch_calendar_events()
            data.unread_emails, data.unread_count = self._fetch_unread_emails()
        except Exception as exc:  # noqa: BLE001 - mostrar error en pantalla
            data.sync_error = str(exc)
        return data

    def _fetch_calendar_events(self) -> list[CalendarEvent]:
        now = datetime.now().astimezone()
        time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
        time_max = time_min + timedelta(days=self.config.days_ahead)

        response = (
            self.calendar.events()
            .list(
                calendarId=self.config.calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            )
            .execute()
        )

        events: list[CalendarEvent] = []
        for item in response.get("items", []):
            start_info = item.get("start", {})
            end_info = item.get("end", {})
            all_day = "date" in start_info

            if all_day:
                start = datetime.fromisoformat(start_info["date"]).replace(tzinfo=timezone.utc)
                end = datetime.fromisoformat(end_info["date"]).replace(tzinfo=timezone.utc)
            else:
                start = datetime.fromisoformat(start_info["dateTime"])
                end = datetime.fromisoformat(end_info["dateTime"])

            events.append(
                CalendarEvent(
                    summary=item.get("summary", "(Sin título)"),
                    start=start,
                    end=end,
                    all_day=all_day,
                    location=item.get("location", ""),
                )
            )
        return events

    def _fetch_unread_emails(self) -> tuple[list[EmailNotification], int]:
        profile = self.gmail.users().getProfile(userId="me").execute()
        unread_count = int(profile.get("messagesUnread", 0))

        response = (
            self.gmail.users()
            .messages()
            .list(
                userId="me",
                q="is:unread in:inbox",
                maxResults=self.config.max_unread_emails,
            )
            .execute()
        )

        notifications: list[EmailNotification] = []
        for item in response.get("messages", []):
            message = (
                self.gmail.users()
                .messages()
                .get(userId="me", id=item["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"])
                .execute()
            )
            headers = {
                header["name"].lower(): header["value"]
                for header in message.get("payload", {}).get("headers", [])
            }
            received_at = self._parse_email_date(headers.get("date", ""))
            notifications.append(
                EmailNotification(
                    sender=self._clean_sender(headers.get("from", "Desconocido")),
                    subject=headers.get("subject", "(Sin asunto)"),
                    received_at=received_at,
                )
            )

        return notifications, unread_count

    @staticmethod
    def _parse_email_date(value: str) -> datetime:
        if not value:
            return datetime.now().astimezone()
        try:
            return parsedate_to_datetime(value).astimezone()
        except (TypeError, ValueError, IndexError):
            return datetime.now().astimezone()

    @staticmethod
    def _clean_sender(raw: str) -> str:
        if "<" in raw:
            return raw.split("<", 1)[0].strip().strip('"') or raw
        return raw
