"""Test screens for the legibility lab, which compares colors, fonts, and layouts."""

import displayio
import terminalio
from adafruit_display_text import label

from src.display_manager import DISPLAY_HEIGHT, DISPLAY_WIDTH
from src.lab_font import DIGITS_3X5, DIGITS_5X7, draw_glyph, draw_segments, fill_rect

# Colors that the matrix shows exactly with 2 bits per channel, in display order
COLOR_LIST = (
    ("white", 0xFFFFFF),
    ("yellow", 0xFFFF00),
    ("cyan", 0x00FFFF),
    ("green", 0x00FF00),
    ("lime", 0xAAFF00),
    ("spring", 0x00FF55),
    ("amber", 0xFFAA00),
    ("orange", 0xFF5500),
    ("red", 0xFF0000),
    ("magenta", 0xFF00FF),
    ("pink", 0xFF55AA),
    ("violet", 0xAA55FF),
    ("blue", 0x0000FF),
    ("sky", 0x55AAFF),
)
COLORS = dict(COLOR_LIST)
COLOR_NAMES = tuple(name for name, _ in COLOR_LIST)

# Dim colors for backgrounds, which draw less current than bright ones
BACKGROUND_LIST = (
    ("black", 0x000000),
    ("navy", 0x000055),
    ("maroon", 0x550000),
    ("dim yellow", 0x555500),
    ("dim cyan", 0x005555),
    ("dim green", 0x005500),
    ("gray", 0x555555),
)
BACKGROUNDS = dict(BACKGROUND_LIST)
BACKGROUND_NAMES = tuple(name for name, _ in BACKGROUND_LIST)

FONT_SEG2 = "seg2"
FONT_SEG3 = "seg3"
FONT_SEG4 = "seg4"
FONT_5X7 = "5x7"
FONT_3X5 = "3x5"
FONT_TERMINAL = "terminal"
FONTS = (FONT_SEG2, FONT_SEG3, FONT_SEG4, FONT_5X7, FONT_3X5, FONT_TERMINAL)

GENDER_NONE = "none"
GENDER_FRAME = "frame"
GENDER_THICK_FRAME = "thick frame"
GENDER_CORNERS = "corners"
GENDER_TINT = "tint"
GENDER_BAR = "bar"
GENDERS = (
    GENDER_NONE,
    GENDER_FRAME,
    GENDER_THICK_FRAME,
    GENDER_CORNERS,
    GENDER_TINT,
    GENDER_BAR,
)
GENDER_COLOR = COLORS["magenta"]
GENDER_TINT_COLOR = 0x550055

MOTION_NONE = "none"
MOTION_MARCH = "march"
MOTION_BLINK = "blink"
MOTION_PULSE = "pulse"
MOTIONS = (MOTION_NONE, MOTION_MARCH, MOTION_BLINK, MOTION_PULSE)

SCORES = (13, 18)

MARGIN = 2
THICK_FRAME_WIDTH = 3
CORNER_SIZE = 5
# Margin that keeps digits clear of a thick frame or corner blocks
THICK_GENDER_MARGIN = 4
DIGIT_WIDTH = 12
DIGIT_GAP = 3
NAMES_HEIGHT = 10
BAR_HEIGHT = 2
DASH_LENGTH = 5
DASH_GAP = 3
MARCH_STEP_SECONDS = 0.1
BLINK_SECONDS = 0.5
PULSE_STEP_SECONDS = 0.25
# Gender color levels, as a fraction of 3, that a pulse steps through
PULSE_LEVELS = (1, 2, 3, 2)

_BLACK, _LEFT, _RIGHT, _LEFT_BG, _RIGHT_BG, _GENDER, _GENDER_OFF = range(7)


class Screen:
    """One test screen: a scoreboard drawn with a given font, colors, and layout.

    A screen with `compare` set asks which half reads better.
    """

    def __init__(
        self,
        screen_id: str,
        title: str,
        font: str = FONT_SEG3,
        left: str = "white",
        right: str = "white",
        names: bool = False,
        gender: str = GENDER_NONE,
        left_bg: str = "black",
        right_bg: str = "black",
        right_font: str | None = None,
        scores: tuple = SCORES,
        motion: str = MOTION_NONE,
        compare: bool = False,
    ):
        self.screen_id = screen_id
        self.title = title
        self.font = font
        self.left = left
        self.right = right
        self.names = names
        self.gender = gender
        self.left_bg = left_bg
        self.right_bg = right_bg
        self.right_font = right_font
        self.scores = scores
        self.motion = motion
        self.compare = compare


class Pair:
    """Two full screens that the viewer switches between to pick the better one."""

    def __init__(self, screen_id: str, title: str, a: Screen, b: Screen):
        self.screen_id = screen_id
        self.title = title
        self.a = a
        self.b = b


def _font_screens() -> list:
    pairs = (
        (FONT_TERMINAL, FONT_SEG3),
        (FONT_TERMINAL, FONT_SEG4),
        (FONT_SEG3, FONT_SEG4),
        (FONT_TERMINAL, FONT_3X5),
        (FONT_TERMINAL, FONT_5X7),
        (FONT_SEG3, FONT_3X5),
    )
    return [
        Screen(
            f"F{i + 1}",
            f"{left} vs {right}",
            font=left,
            right_font=right,
            scores=(18, 18),
            compare=True,
        )
        for i, (left, right) in enumerate(pairs)
    ]


def _gender_screen(gender: str, motion: str = MOTION_NONE) -> Screen:
    title = gender if motion == MOTION_NONE else f"{gender}, {motion}"
    return Screen(
        "",
        title,
        font=FONT_TERMINAL,
        left="yellow",
        right="cyan",
        gender=gender,
        motion=motion,
    )


def _gender_pairs() -> list:
    thick = _gender_screen(GENDER_THICK_FRAME)
    others = (
        (_gender_screen(GENDER_FRAME), thick),
        (thick, _gender_screen(GENDER_CORNERS)),
        (thick, _gender_screen(GENDER_TINT)),
        (thick, _gender_screen(GENDER_THICK_FRAME, MOTION_MARCH)),
        (thick, _gender_screen(GENDER_THICK_FRAME, MOTION_BLINK)),
        (thick, _gender_screen(GENDER_THICK_FRAME, MOTION_PULSE)),
    )
    return [
        Pair(f"G{i + 1}", f"{a.title} vs {b.title}", a, b)
        for i, (a, b) in enumerate(others)
    ]


def _team_screen(left: str, right: str, left_bg="black", right_bg="black") -> Screen:
    title = f"{left}/{right}"
    if left_bg != "black" or right_bg != "black":
        title += f" on {left_bg}/{right_bg}"
    return Screen(
        "",
        title,
        font=FONT_TERMINAL,
        left=left,
        right=right,
        left_bg=left_bg,
        right_bg=right_bg,
    )


def _team_pairs() -> list:
    current = _team_screen("yellow", "cyan")
    white_on_halves = _team_screen("white", "white", "navy", "maroon")
    pairs = (
        (current, _team_screen("white", "orange")),
        (current, _team_screen("yellow", "sky")),
        (current, _team_screen("white", "amber")),
        (current, white_on_halves),
        (white_on_halves, _team_screen("white", "white", "navy", "dim green")),
        (white_on_halves, _team_screen("yellow", "cyan", "navy", "maroon")),
    )
    return [
        Pair(f"T{i + 1}", f"{a.title} vs {b.title}", a, b)
        for i, (a, b) in enumerate(pairs)
    ]


def round_two_screens() -> list:
    """Return the second round of screens and pairs, in the order the lab shows them."""
    return _font_screens() + _gender_pairs() + _team_pairs()


def _draw_digit(
    bitmap, font: str, digit: str, x: int, y: int, height: int, index: int
) -> None:
    if font.startswith("seg"):
        stroke = int(font[3:])
        draw_segments(bitmap, digit, x, y, DIGIT_WIDTH, height, stroke, index)
        return
    rows = DIGITS_5X7[digit] if font == FONT_5X7 else DIGITS_3X5[digit]
    columns = len(rows[0])
    scale_x = DIGIT_WIDTH // columns
    scale_y = height // len(rows)
    draw_glyph(
        bitmap,
        rows,
        x + (DIGIT_WIDTH - columns * scale_x) // 2,
        y + (height - len(rows) * scale_y) // 2,
        scale_x,
        scale_y,
        index,
    )


def _scaled_color(color: int, level: int) -> int:
    """Return `color` with each channel scaled to `level` thirds of its value."""
    return (
        ((color >> 16 & 0xFF) * level // 3) << 16
        | ((color >> 8 & 0xFF) * level // 3) << 8
        | (color & 0xFF) * level // 3
    )


def _frame_pixels(width: int) -> tuple[list, list]:
    """Return the (x, y) pixels of a frame `width` thick, and the distance of each
    along the outer edge, clockwise from the top-left corner."""
    pixels = []
    distances = []
    right, bottom = DISPLAY_WIDTH - 1, DISPLAY_HEIGHT - 1
    for y in range(DISPLAY_HEIGHT):
        for x in range(DISPLAY_WIDTH):
            depth = min(x, y, right - x, bottom - y)
            if depth >= width:
                continue
            if y == depth and x < right - depth:
                distance = x
            elif x == right - depth and y < bottom - depth:
                distance = right + y
            elif y == bottom - depth and x > depth:
                distance = right + bottom + (right - x)
            else:
                distance = 2 * right + bottom + (bottom - y)
            pixels.append((x, y))
            distances.append(distance)
    return pixels, distances


class DrawnScreen:
    """A screen drawn into a display group, which `animate` moves over time."""

    def __init__(self, screen: Screen):
        self.screen = screen
        self.group = displayio.Group()
        self._palette = displayio.Palette(7)
        self._bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 7)
        self._frame: list = []
        self._frame_distances: list = []
        self._step = -1
        self._pulse_colors = [
            _scaled_color(GENDER_COLOR, level) for level in PULSE_LEVELS
        ]
        self._draw()

    def _draw(self) -> None:
        screen = self.screen
        palette = self._palette
        bitmap = self._bitmap
        palette[_BLACK] = 0x000000
        palette[_LEFT] = COLORS[screen.left]
        palette[_RIGHT] = COLORS[screen.right]
        palette[_LEFT_BG] = BACKGROUNDS[screen.left_bg]
        palette[_RIGHT_BG] = BACKGROUNDS[screen.right_bg]
        palette[_GENDER] = GENDER_COLOR
        palette[_GENDER_OFF] = BACKGROUNDS[screen.left_bg]
        if screen.gender == GENDER_TINT:
            palette[_LEFT_BG] = GENDER_TINT_COLOR
            palette[_RIGHT_BG] = GENDER_TINT_COLOR
        half = DISPLAY_WIDTH // 2
        fill_rect(bitmap, 0, 0, half, DISPLAY_HEIGHT, _LEFT_BG)
        fill_rect(bitmap, half, 0, half, DISPLAY_HEIGHT, _RIGHT_BG)
        self.group.append(displayio.TileGrid(bitmap, pixel_shader=palette))

        thick = screen.gender in {GENDER_THICK_FRAME, GENDER_CORNERS}
        margin = THICK_GENDER_MARGIN if thick else MARGIN
        half_width = half - margin - 1
        top = NAMES_HEIGHT if screen.names else margin
        height = DISPLAY_HEIGHT - margin - top
        right_font = screen.right_font or screen.font
        halves = (
            (margin, screen.scores[0], _LEFT, screen.left, screen.font),
            (half + 1, screen.scores[1], _RIGHT, screen.right, right_font),
        )
        for half_x, score, index, color_name, font in halves:
            text = str(score)
            if font == FONT_TERMINAL:
                self.group.append(
                    label.Label(
                        terminalio.FONT,
                        text=text,
                        scale=2,
                        color=COLORS[color_name],
                        anchor_point=(0.5, 0.5),
                        anchored_position=(half_x + half_width // 2, top + height // 2),
                    )
                )
                continue
            width = len(text) * DIGIT_WIDTH + (len(text) - 1) * DIGIT_GAP
            x = half_x + (half_width - width) // 2
            for digit in text:
                _draw_digit(bitmap, font, digit, x, top, height, index)
                x += DIGIT_WIDTH + DIGIT_GAP

        if screen.gender == GENDER_FRAME:
            self._frame, self._frame_distances = _frame_pixels(1)
        elif screen.gender == GENDER_THICK_FRAME:
            self._frame, self._frame_distances = _frame_pixels(THICK_FRAME_WIDTH)
        for pixel in self._frame:
            bitmap[pixel] = _GENDER
        if screen.gender == GENDER_CORNERS:
            right = DISPLAY_WIDTH - CORNER_SIZE
            bottom = DISPLAY_HEIGHT - CORNER_SIZE
            for x, y in ((0, 0), (right, 0), (0, bottom), (right, bottom)):
                fill_rect(bitmap, x, y, CORNER_SIZE, CORNER_SIZE, _GENDER)
        elif screen.gender == GENDER_BAR:
            fill_rect(
                bitmap,
                0,
                DISPLAY_HEIGHT - BAR_HEIGHT,
                DISPLAY_WIDTH,
                BAR_HEIGHT,
                _GENDER,
            )

        if screen.names:
            for text, color_name, anchor_x, x in (
                ("AWAY", screen.left, 0.0, margin),
                ("HOME", screen.right, 1.0, DISPLAY_WIDTH - 1),
            ):
                self.group.append(
                    label.Label(
                        terminalio.FONT,
                        text=text,
                        color=COLORS[color_name],
                        anchor_point=(anchor_x, 0.0),
                        anchored_position=(x, 0),
                    )
                )

    def animate(self, elapsed: float) -> None:
        """Move the gender indicator to where it is `elapsed` seconds after the screen showed."""
        motion = self.screen.motion
        if motion == MOTION_MARCH:
            step = int(elapsed / MARCH_STEP_SECONDS) % (DASH_LENGTH + DASH_GAP)
            if step == self._step:
                return
            self._step = step
            frame = self._frame
            distances = self._frame_distances
            period = DASH_LENGTH + DASH_GAP
            for i in range(len(frame)):
                lit = (distances[i] - step) % period < DASH_LENGTH
                self._bitmap[frame[i]] = _GENDER if lit else _GENDER_OFF
        elif motion == MOTION_BLINK:
            on = int(elapsed / BLINK_SECONDS) % 2 == 0
            self._palette[_GENDER] = (
                GENDER_COLOR if on else BACKGROUNDS[self.screen.left_bg]
            )
        elif motion == MOTION_PULSE:
            step = int(elapsed / PULSE_STEP_SECONDS) % len(PULSE_LEVELS)
            self._palette[_GENDER] = self._pulse_colors[step]
