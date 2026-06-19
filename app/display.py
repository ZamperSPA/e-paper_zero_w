"""Control del display e-paper Waveshare 2.7\" HAT monocromo V2."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import DisplayConfig

logger = logging.getLogger(__name__)

WHITE = 255
BLACK = 0


class EpaperDisplay:
    WIDTH = 176
    HEIGHT = 264

    def __init__(self, config: DisplayConfig) -> None:
        self.config = config
        self.mock = config.mock
        self._epd = None

        if not self.mock:
            try:
                from waveshare_epd import epd2in7_V2

                self._epd = epd2in7_V2.EPD()
            except ImportError as exc:
                raise ImportError(
                    "Instala los drivers de Waveshare:\n"
                    "  git clone https://github.com/waveshare/e-Paper.git\n"
                    "  cd e-Paper/RaspberryPi_JetsonNano/python && pip install ."
                ) from exc

        self.font_title = self._load_font(config.font_bold, 14)
        self.font_bold = self._load_font(config.font_bold, 11)
        self.font_body = self._load_font(config.font_regular, 11)
        self.font_small = self._load_font(config.font_regular, 9)
        self.font_hint = self._load_font(config.font_regular, 8)

    def init(self) -> None:
        if self._epd is None:
            return
        if self._epd.init() != 0:
            raise RuntimeError("No se pudo inicializar el e-paper HAT")
        self._epd.Clear()

    def sleep(self) -> None:
        if self._epd is not None:
            self._epd.sleep()

    def show(self, image: Image.Image) -> None:
        if self.mock:
            preview = self._to_rgb(image)
            preview.save(self.config.mock_output)
            logger.info("Vista previa guardada en %s", self.config.mock_output)
            return

        assert self._epd is not None
        self._epd.display(self._epd.getbuffer(image))

    def blank_canvas(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("1", (self.WIDTH, self.HEIGHT), WHITE)
        return image, ImageDraw.Draw(image)

    @staticmethod
    def _load_font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if path.exists():
            return ImageFont.truetype(str(path), size)
        logger.warning("Fuente no encontrada (%s), usando fuente por defecto", path)
        return ImageFont.load_default()

    @staticmethod
    def _to_rgb(layer: Image.Image) -> Image.Image:
        rgb = Image.new("RGB", layer.size, "white")
        pixels = layer.load()
        out = rgb.load()
        for y in range(layer.height):
            for x in range(layer.width):
                if pixels[x, y] == BLACK:
                    out[x, y] = (0, 0, 0)
        return rgb

    def draw_header(self, draw: ImageDraw.ImageDraw, title: str, subtitle: str = "") -> int:
        draw.rectangle((0, 0, self.WIDTH, 28), fill=BLACK)
        draw.text((6, 6), title, font=self.font_title, fill=WHITE)
        if subtitle:
            draw.text((6, 18), subtitle, font=self.font_hint, fill=WHITE)
        return 32

    def draw_section_title(self, draw: ImageDraw.ImageDraw, y: int, text: str) -> int:
        draw.text((6, y), text, font=self.font_bold, fill=BLACK)
        draw.line((6, y + 12, self.WIDTH - 6, y + 12), fill=BLACK, width=1)
        return y + 16

    def draw_footer_hints(self, draw: ImageDraw.ImageDraw, hints: str) -> None:
        y = self.HEIGHT - 14
        draw.line((0, y - 2, self.WIDTH, y - 2), fill=BLACK, width=1)
        draw.text((4, y), hints, font=self.font_hint, fill=BLACK)

    def wrap_text(
        self,
        text: str,
        font: ImageFont.ImageFont,
        max_width: int,
    ) -> list[str]:
        words = text.split()
        if not words:
            return [""]

        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if font.getlength(candidate) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def draw_text_block(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        lines: list[str],
        font: ImageFont.ImageFont,
        fill: int = BLACK,
        line_height: int = 12,
        max_lines: int | None = None,
    ) -> int:
        visible = lines[:max_lines] if max_lines else lines
        for index, line in enumerate(visible):
            draw.text((x, y + index * line_height), line, font=font, fill=fill)
        return y + len(visible) * line_height
