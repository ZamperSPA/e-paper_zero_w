"""Renderizado de pantallas del calendario y notificaciones."""

from __future__ import annotations

from datetime import date

from app.display import EpaperDisplay
from app.models import AppState, Screen


class ScreenRenderer:
    MONTHS_ES = (
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    )
    WEEKDAYS_ES = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")

    def __init__(self, display: EpaperDisplay) -> None:
        self.display = display

    def render(self, state: AppState) -> None:
        if state.screen == Screen.CALENDAR_DAY:
            layers = self._render_day_view(state)
        elif state.screen == Screen.CALENDAR_AGENDA:
            layers = self._render_agenda_view(state)
        else:
            layers = self._render_notifications_view(state)

        self.display.show(*layers)

    def _render_day_view(self, state: AppState):
        black, red, draw_black, draw_red = self.display.blank_canvas()
        day = state.selected_day
        title = self._format_day_title(day)
        is_today = day == date.today()

        subtitle = "Hoy" if is_today else self.WEEKDAYS_ES[day.weekday()]
        y = self.display.draw_header(draw_black, draw_red, title, subtitle)

        if state.data.sync_error:
            y = self._draw_error(draw_black, draw_red, y, state.data.sync_error)
        else:
            events = state.events_for_day(day)
            if not events:
                draw_black.text((8, y + 8), "Sin eventos", font=self.display.font_body, fill=0)
            else:
                y = self._draw_events(draw_black, draw_red, y, events)

        self.display.draw_footer_hints(
            draw_black,
            "K1:día- K2:día+ K3:sync K4:agenda",
        )
        return black, red

    def _render_agenda_view(self, state: AppState):
        black, red, draw_black, draw_red = self.display.blank_canvas()
        y = self.display.draw_header(draw_black, draw_red, "Agenda", "Próximos días")

        if state.data.sync_error:
            y = self._draw_error(draw_black, draw_red, y, state.data.sync_error)
        else:
            current_day: date | None = None
            for event in state.data.upcoming_events(limit=10):
                event_day = event.start.date()
                if event_day != current_day:
                    current_day = event_day
                    draw_red.text(
                        (6, y),
                        self._format_day_title(event_day),
                        font=self.display.font_body,
                        fill=0,
                    )
                    y += 14

                time_label = self._format_event_time(event)
                line = f"{time_label} {event.summary}"
                wrapped = self.display.wrap_text(line, self.display.font_small, 160)
                y = self.display.draw_text_block(
                    draw_black, 8, y, wrapped[:2], self.display.font_small, max_lines=2
                )
                y += 2
                if y > self.display.HEIGHT - 24:
                    break

            if not state.data.events:
                draw_black.text((8, y + 8), "Sin eventos próximos", font=self.display.font_body, fill=0)

        self.display.draw_footer_hints(
            draw_black,
            "K1:día K2:día+ K3:sync K4:notif",
        )
        return black, red

    def _render_notifications_view(self, state: AppState):
        black, red, draw_black, draw_red = self.display.blank_canvas()
        unread = state.data.unread_count
        y = self.display.draw_header(
            draw_black,
            draw_red,
            "Notificaciones",
            f"{unread} correo(s) sin leer",
        )

        if state.data.sync_error:
            y = self._draw_error(draw_black, draw_red, y, state.data.sync_error)
        else:
            draw_red.text((6, y), "Próximos eventos", font=self.display.font_body, fill=0)
            y += 14
            for event in state.data.upcoming_events(limit=3):
                label = f"{self._format_event_time(event)} {event.summary}"
                wrapped = self.display.wrap_text(label, self.display.font_small, 160)
                y = self.display.draw_text_block(
                    draw_black, 8, y, wrapped[:1], self.display.font_small, max_lines=1
                )
                y += 2

            y += 4
            draw_red.text((6, y), "Gmail sin leer", font=self.display.font_body, fill=0)
            y += 14

            if not state.data.unread_emails:
                draw_black.text((8, y), "Bandeja al día", font=self.display.font_small, fill=0)
            else:
                for email in state.data.unread_emails:
                    sender_lines = self.display.wrap_text(
                        email.sender, self.display.font_small, 160
                    )
                    subject_lines = self.display.wrap_text(
                        email.subject, self.display.font_small, 160
                    )
                    draw_black.text((8, y), sender_lines[0], font=self.display.font_small, fill=0)
                    y += 11
                    draw_black.text((8, y), subject_lines[0], font=self.display.font_hint, fill=0)
                    y += 13
                    if y > self.display.HEIGHT - 28:
                        break

        self.display.draw_footer_hints(
            draw_black,
            "K1:calend K2:día+ K3:sync K4:agenda",
        )
        return black, red

    def _draw_events(self, draw_black, draw_red, y, events):
        for event in events:
            time_label = self._format_event_time(event)
            draw_red.text((6, y), time_label, font=self.display.font_body, fill=0)
            y += 13

            wrapped = self.display.wrap_text(event.summary, self.display.font_body, 160)
            y = self.display.draw_text_block(
                draw_black, 8, y, wrapped[:2], self.display.font_body, max_lines=2
            )

            if event.location:
                location_lines = self.display.wrap_text(
                    event.location, self.display.font_small, 156
                )
                y = self.display.draw_text_block(
                    draw_black, 10, y, location_lines[:1], self.display.font_small, max_lines=1
                )

            y += 6
            if y > self.display.HEIGHT - 30:
                draw_black.text((8, y), "...", font=self.display.font_small, fill=0)
                break
        return y

    def _draw_error(self, draw_black, draw_red, y, message: str):
        lines = self.display.wrap_text(message, self.display.font_small, 160)
        return self.display.draw_text_block(
            draw_red, 8, y + 8, lines[:6], self.display.font_small, fill=0
        )

    def _format_day_title(self, day: date) -> str:
        month = self.MONTHS_ES[day.month - 1]
        return f"{day.day} {month} {day.year}"

    @staticmethod
    def _format_event_time(event) -> str:
        if event.all_day:
            return "Todo el día"
        start = event.start.astimezone()
        end = event.end.astimezone()
        return f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
