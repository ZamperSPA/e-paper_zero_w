"""Control del display e-paper Waveshare 2.7\" HAT monocromo V1."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import DisplayConfig

logger = logging.getLogger(__name__)

WHITE = 255
BLACK = 0

LINUX_FONT_CANDIDATES: dict[str, list[Path]] = {
    "regular": [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    ],
    "bold": [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ],
}


class EpaperDisplay:
    WIDTH = 176
    HEIGHT = 264

    def __init__(self, config: DisplayConfig) -> None:
        self.config = config
        self.mock = config.mock
        self._epd = None
        self._frame_count = 0

        if not self.mock:
            try:
                from waveshare_epd import epd2in7

                self._epd = epd2in7.EPD()
            except ImportError as exc:
                missing = getattr(exc, "name", "") or str(exc)
                if "spidev" in missing:
                    raise ImportError(
                        "Falta el módulo spidev (comunicación SPI con el HAT).\n"
                        "Con el entorno virtual activado:\n"
                        "  pip install spidev\n"
                        "O reinstala dependencias:\n"
                        "  pip install -r requirements.txt"
                    ) from exc
                raise ImportError(
                    "Instala los drivers de Waveshare en el mismo venv:\n"
                    "  git clone https://github.com/waveshare/e-Paper.git\n"
                    "  cd e-Paper/RaspberryPi_JetsonNano/python && pip install ."
                ) from exc

        self.font_title = self._load_font(config.font_bold, 14, "bold")
        self.font_bold = self._load_font(config.font_bold, 11, "bold")
        self.font_body = self._load_font(config.font_regular, 11, "regular")
        self.font_small = self._load_font(config.font_regular, 9, "regular")
        self.font_hint = self._load_font(config.font_regular, 8, "regular")
        self.font_welcome = self._load_font(config.font_bold, 18, "bold")

    def init(self) -> None:
        if self._epd is None:
            return
        logger.info("Inicializando e-paper...")
        if self._epd.init() != 0:
            raise RuntimeError("No se pudo inicializar el e-paper HAT")
        self._epd.Clear(0xFF)
        self._frame_count = 0
        logger.info("e-paper listo (driver V1)")

    def sleep(self) -> None:
        if self._epd is not None:
            self._epd.sleep()

    def show(self, image: Image.Image, *, full_refresh: bool = False) -> None:
        if self.mock:
            preview = self._to_rgb(image)
            preview.save(self.config.mock_output)
            logger.info("Vista previa guardada en %s", self.config.mock_output)
            return

        assert self._epd is not None
        if image.size != (self.WIDTH, self.HEIGHT):
            image = image.resize((self.WIDTH, self.HEIGHT))

        buffer = self._epd.getbuffer(image)
        use_full = full_refresh or self._frame_count == 0

        logger.info(
            "Actualizando pantalla V1 (%s, puede tardar ~15 s)...",
            "refresco completo" if use_full else "actualización",
        )

        if use_full and self._epd.init() != 0:
            raise RuntimeError("No se pudo reinicializar el e-paper")

        self._epd.display(buffer)

        self._frame_count += 1
        logger.info("Pantalla actualizada")

    def blank_canvas(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("1", (self.WIDTH, self.HEIGHT), WHITE)
        return image, ImageDraw.Draw(image)

    @classmethod
    def _resolve_font_path(cls, path: Path, kind: str) -> Path | None:
        if path.exists():
            return path
        for candidate in LINUX_FONT_CANDIDATES.get(kind, []):
            if candidate.exists():
                logger.info("Usando fuente alternativa: %s", candidate)
                return candidate
        return None

    @classmethod
    def _load_font(
        cls,
        path: Path,
        size: int,
        kind: str = "regular",
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        resolved = cls._resolve_font_path(path, kind)
        if resolved is not None:
            return ImageFont.truetype(str(resolved), size)
        logger.warning(
            "Fuente no encontrada (%s). Instala: sudo apt install fonts-dejavu-core",
            path,
        )
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

    def draw_footer_hints(
        self,
        draw: ImageDraw.ImageDraw,
        hints: str,
        feedback: str = "",
    ) -> None:
        if feedback:
            y = self.HEIGHT - 28
            draw.rectangle((0, y, self.WIDTH, self.HEIGHT), fill=BLACK)
            draw.text((4, y + 4), hints, font=self.font_hint, fill=WHITE)
            draw.text((4, y + 14), feedback, font=self.font_hint, fill=WHITE)
            return

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

    def draw_centered_text(
        self,
        draw: ImageDraw.ImageDraw,
        y: int,
        text: str,
        font: ImageFont.ImageFont,
        fill: int = BLACK,
    ) -> None:
        width = font.getlength(text)
        x = max(0, int((self.WIDTH - width) / 2))
        draw.text((x, y), text, font=font, fill=fill)
