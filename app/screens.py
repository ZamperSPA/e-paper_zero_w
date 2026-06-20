"""Renderizado de pantallas del calendario y notificaciones."""

from __future__ import annotations

from datetime import date

from app.display import BLACK, WHITE, EpaperDisplay
from app.models import AppState, Screen


class ScreenRenderer:
    MONTHS_ES = (
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    )
    WEEKDAYS_ES = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")

    def __init__(self, display: EpaperDisplay) -> None:
        self.display = display

    def render_welcome(self) -> None:
        image, draw = self.display.blank_canvas()
        draw.rectangle((0, 0, self.display.WIDTH, self.display.HEIGHT), fill=BLACK)
        self.display.draw_centered_text(draw, 95, "e-Paper", self.display.font_welcome, fill=WHITE)
        self.display.draw_centered_text(draw, 125, "Calendario", self.display.font_bold, fill=WHITE)
        self.display.draw_centered_text(draw, 155, "Gmail", self.display.font_body, fill=WHITE)
        self.display.draw_centered_text(draw, 200, "Iniciando...", self.display.font_hint, fill=WHITE)
        draw.rectangle((20, 220, self.display.WIDTH - 20, 228), outline=WHITE)
        draw.rectangle((20, 220, 60, 228), fill=WHITE)
        self.display.show(image, full_refresh=True)

    def render(self, state: AppState) -> None:
        if state.screen == Screen.CALENDAR_DAY:
            image = self._render_day_view(state)
        elif state.screen == Screen.CALENDAR_AGENDA:
            image = self._render_agenda_view(state)
        else:
            image = self._render_notifications_view(state)

        self.display.show(image)

    def _footer(self, draw, hints: str, state: AppState) -> None:
        feedback = f"● {state.button_feedback}" if state.button_feedback else ""
        self.display.draw_footer_hints(draw, hints, feedback=feedback)

    def _render_day_view(self, state: AppState):
        image, draw = self.display.blank_canvas()
        day = state.selected_day
        title = self._format_day_title(day)
        is_today = day == date.today()

        subtitle = "Hoy" if is_today else self.WEEKDAYS_ES[day.weekday()]
        y = self.display.draw_header(draw, title, subtitle)

        if state.data.sync_error:
            y = self._draw_error(draw, y, state.data.sync_error)
        else:
            events = state.events_for_day(day)
            if not events:
                draw.text((8, y + 8), "Sin eventos", font=self.display.font_body, fill=0)
            else:
                y = self._draw_events(draw, y, events)

        self._footer(draw, "K1:día- K2:día+ K3:sync K4:agenda", state)
        return image

    def _render_agenda_view(self, state: AppState):
        image, draw = self.display.blank_canvas()
        y = self.display.draw_header(draw, "Agenda", "Próximos días")

        if state.data.sync_error:
            y = self._draw_error(draw, y, state.data.sync_error)
        else:
            upcoming = state.upcoming_events(limit=10)
            if not upcoming:
                draw.text((8, y + 8), "Sin eventos", font=self.display.font_body, fill=0)
            else:
                current_day: date | None = None
                for event in upcoming:
                    event_day = event.start.date()
                    if event_day != current_day:
                        current_day = event_day
                        y = self.display.draw_section_title(draw, y, self._format_day_title(event_day))

                    time_label = self._format_event_time(event)
                    line = f"{time_label} {event.summary}"
                    wrapped = self.display.wrap_text(line, self.display.font_small, 160)
                    y = self.display.draw_text_block(
                        draw, 8, y, wrapped[:2], self.display.font_small, max_lines=2
                    )
                    y += 2
                    if y > self.display.HEIGHT - 36:
                        break

        self._footer(draw, "K1:día K2:día+ K3:sync K4:notif", state)
        return image

    def _render_notifications_view(self, state: AppState):
        image, draw = self.display.blank_canvas()
        unread = state.data.unread_count
        y = self.display.draw_header(
            draw,
            "Notificaciones",
            f"{unread} correo(s) sin leer",
        )

        if state.data.sync_error:
            y = self._draw_error(draw, y, state.data.sync_error)
        else:
            upcoming = state.upcoming_events(limit=3)
            has_emails = bool(state.data.unread_emails)

            if not upcoming and not has_emails:
                draw.text((8, y + 8), "Sin notificaciones", font=self.display.font_body, fill=0)
            else:
                y = self.display.draw_section_title(draw, y, "Próximos eventos")
                if not upcoming:
                    draw.text((8, y), "Sin eventos", font=self.display.font_small, fill=0)
                    y += 14
                else:
                    for event in upcoming:
                        label = f"{self._format_event_time(event)} {event.summary}"
                        wrapped = self.display.wrap_text(label, self.display.font_small, 160)
                        y = self.display.draw_text_block(
                            draw, 8, y, wrapped[:1], self.display.font_small, max_lines=1
                        )
                        y += 2

                y += 4
                y = self.display.draw_section_title(draw, y, "Gmail sin leer")

                if not has_emails:
                    draw.text((8, y), "Bandeja al día", font=self.display.font_small, fill=0)
                else:
                    for email in state.data.unread_emails:
                        sender_lines = self.display.wrap_text(
                            email.sender, self.display.font_small, 160
                        )
                        subject_lines = self.display.wrap_text(
                            email.subject, self.display.font_small, 160
                        )
                        draw.text((8, y), sender_lines[0], font=self.display.font_bold, fill=0)
                        y += 11
                        draw.text((8, y), subject_lines[0], font=self.display.font_hint, fill=0)
                        y += 13
                        if y > self.display.HEIGHT - 36:
                            break

        self._footer(draw, "K1:calend K2:día+ K3:sync K4:agenda", state)
        return image

    def _draw_events(self, draw, y, events):
        for event in events:
            time_label = self._format_event_time(event)
            draw.text((6, y), time_label, font=self.display.font_bold, fill=0)
            y += 13

            wrapped = self.display.wrap_text(event.summary, self.display.font_body, 160)
            y = self.display.draw_text_block(
                draw, 8, y, wrapped[:2], self.display.font_body, max_lines=2
            )

            if event.location:
                location_lines = self.display.wrap_text(
                    event.location, self.display.font_small, 156
                )
                y = self.display.draw_text_block(
                    draw, 10, y, location_lines[:1], self.display.font_small, max_lines=1
                )

            y += 6
            if y > self.display.HEIGHT - 30:
                draw.text((8, y), "...", font=self.display.font_small, fill=0)
                break
        return y

    def _draw_error(self, draw, y, message: str):
        lines = self.display.wrap_text(message, self.display.font_small, 160)
        draw.rectangle((4, y + 4, self.display.WIDTH - 4, y + 4 + len(lines[:6]) * 12 + 8), outline=0)
        return self.display.draw_text_block(
            draw, 8, y + 8, lines[:6], self.display.font_small, fill=0
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
