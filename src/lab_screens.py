"""Test screens for the legibility lab, which compares colors, fonts, and layouts."""

import displayio
import terminalio
from adafruit_display_text import label

from src.display_manager import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    WMP_FRAME_MARCH_SECONDS,
    DisplayManager,
)
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
GENDER_TINT_COLOR = 0x550055

MOTION_NONE = "none"
MOTION_DASHES = "dashes"
MOTION_MARCH = "march"
MOTION_MARCH_THEN_HOLD = "march 30 s"
MOTION_BLINK = "blink"
MOTION_PULSE = "pulse"
MOTIONS = (
    MOTION_NONE,
    MOTION_DASHES,
    MOTION_MARCH,
    MOTION_MARCH_THEN_HOLD,
    MOTION_BLINK,
    MOTION_PULSE,
)
_DASHED_MOTIONS = (MOTION_DASHES, MOTION_MARCH, MOTION_MARCH_THEN_HOLD)

LABEL_NONE = "none"
LABEL_STACKED = "stacked"
LABEL_UNDER = "under"
LABELS = (LABEL_NONE, LABEL_STACKED, LABEL_UNDER)

LAYOUT_LAB = "lab"
LAYOUT_CURRENT = "current"


SCORES = (13, 18)

MARGIN = 2
THICK_FRAME_WIDTH = 3
CORNER_SIZE = 5
# Margin that keeps digits clear of a thick frame or corner blocks
THICK_GENDER_MARGIN = 4
DIGIT_WIDTH = 12
DIGIT_GAP = 3
NAMES_HEIGHT = 10
# Rows and columns between a terminal font label's anchor box and its lit pixels
SMALL_INK_TOP = 2
SMALL_INK_HEIGHT = 8
SMALL_INK_RIGHT_PAD = 1
LARGE_INK_TOP = 4
LARGE_INK_HEIGHT = 16
LARGE_INK_LEFT = 2
LARGE_INK_RIGHT_PAD = 2
INK_GAP = 1
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
        gender_color: str = "magenta",
        label: str = "",
        label_style: str = LABEL_NONE,
        layout: str = LAYOUT_LAB,
        bold: bool = False,
        names_level: int = 3,
        gender_level: int = 3,
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
        self.gender_color = gender_color
        self.label = label
        self.label_style = label_style
        self.layout = layout
        self.bold = bold
        self.names_level = names_level
        self.gender_level = gender_level


class Pair:
    """Two full screens that the viewer switches between to answer `question`."""

    def __init__(self, screen_id: str, title: str, question: str, a: Screen, b: Screen):
        self.screen_id = screen_id
        self.title = title
        self.question = question
        self.a = a
        self.b = b


def _scoreboard(
    title: str,
    gender: str = "W",
    gender_color: str = "cyan",
) -> Screen:
    """Return the design that earlier rounds picked, with a given gender frame.

    A gender_color of "none" leaves out the frame.
    """
    framed = gender_color != "none"
    return Screen(
        "",
        title,
        font=FONT_TERMINAL,
        left="yellow",
        right="white",
        names=True,
        names_level=2,
        bold=True,
        gender=GENDER_THICK_FRAME if framed else GENDER_NONE,
        gender_color=gender_color if framed else "white",
        motion=MOTION_MARCH_THEN_HOLD if gender == "W" else MOTION_DASHES,
        label=f"{gender}1",
        label_style=LABEL_STACKED,
    )


def _round_robin(prefix: str, question: str, screens: tuple) -> list:
    """Return a Pair for every two of `screens`."""
    pairs = []
    for i in range(len(screens)):
        for j in range(i + 1, len(screens)):
            a, b = screens[i], screens[j]
            pairs.append(
                Pair(
                    f"{prefix}{len(pairs) + 1}",
                    f"{a.title} vs {b.title}",
                    question,
                    a,
                    b,
                )
            )
    return pairs


def round_five_screens() -> list:
    """Return the fifth round of pairs, in the order the lab shows them."""
    wmp = tuple(
        _scoreboard(f"WMP {c}", gender_color=c) for c in ("cyan", "sky", "lime")
    )
    mmp = tuple(
        _scoreboard(f"MMP {c} frame" if c != "none" else "MMP no frame", "M", c)
        for c in ("white", "amber", "none")
    )
    question = "From the far end zone, which score can you read?"
    current = (
        Screen("", "current scoreboard, WMP", layout=LAYOUT_CURRENT, label="W1"),
        Screen("", "current scoreboard, MMP", layout=LAYOUT_CURRENT, label="M1"),
    )
    final = (
        Pair("F1", "current vs new, WMP", question, current[0], wmp[0]),
        Pair("F2", "current vs new, MMP", question, current[1], mmp[0]),
    )
    return (
        _round_robin(
            "W", "From the far end zone, which WMP frame do you notice faster?", wmp
        )
        + _round_robin("M", "For MMP points, which would you rather see all game?", mmp)
        + list(final)
    )


class _Capture:
    """Holds the root group that a DisplayManager sets, in place of a MatrixPortal."""

    def __init__(self):
        self.display = self
        self.root_group = None


def _current_scoreboard(gender: str) -> tuple:
    """Return a DisplayManager that shows a point for `gender`, and its root group.

    :param gender: "W" or "M"
    """
    capture = _Capture()
    display_manager = DisplayManager(capture)
    display_manager.set_team_names("AWAY", "HOME")
    display_manager.set_scores(*SCORES)
    display_manager.set_gender_matchup(f"{gender}MP", 1)
    display_manager.march_wmp_frame()
    return display_manager, capture.root_group


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
        self._gender_color = _scaled_color(
            COLORS[screen.gender_color], screen.gender_level
        )
        self._palette = displayio.Palette(7)
        self._bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 7)
        self._frame: list = []
        self._frame_distances: list = []
        self._step = -1
        self._pulse_colors = [
            _scaled_color(self._gender_color, level) for level in PULSE_LEVELS
        ]
        self._current: DisplayManager | None = None
        if screen.layout == LAYOUT_CURRENT:
            self._current, self.group = _current_scoreboard(screen.label[:1] or "W")
        else:
            self.group = displayio.Group()
            self._draw()

    def _draw(self) -> None:
        screen = self.screen
        palette = self._palette
        palette[_BLACK] = 0x000000
        palette[_LEFT] = COLORS[screen.left]
        palette[_RIGHT] = COLORS[screen.right]
        palette[_LEFT_BG] = BACKGROUNDS[screen.left_bg]
        palette[_RIGHT_BG] = BACKGROUNDS[screen.right_bg]
        palette[_GENDER] = self._gender_color
        palette[_GENDER_OFF] = BACKGROUNDS[screen.left_bg]
        if screen.gender == GENDER_TINT:
            palette[_LEFT_BG] = GENDER_TINT_COLOR
            palette[_RIGHT_BG] = GENDER_TINT_COLOR
        half = DISPLAY_WIDTH // 2
        fill_rect(self._bitmap, 0, 0, half, DISPLAY_HEIGHT, _LEFT_BG)
        fill_rect(self._bitmap, half, 0, half, DISPLAY_HEIGHT, _RIGHT_BG)
        self.group.append(displayio.TileGrid(self._bitmap, pixel_shader=palette))
        if screen.font == FONT_TERMINAL and screen.right_font in {None, FONT_TERMINAL}:
            self._draw_terminal_layout()
        else:
            self._draw_large_digits()
        self._draw_gender()

    def _add_text(self, text: str, scale: int, color: int, anchor, position) -> None:
        self.group.append(
            label.Label(
                terminalio.FONT,
                text=text,
                scale=scale,
                color=color,
                anchor_point=anchor,
                anchored_position=position,
            )
        )

    def _draw_terminal_layout(self) -> None:
        """Lay out names, scores, and the matchup label by where their pixels light."""
        screen = self.screen
        frame_width = {GENDER_FRAME: 1, GENDER_THICK_FRAME: THICK_FRAME_WIDTH}.get(
            screen.gender, 0
        )
        inset = max(frame_width + 1, MARGIN)
        under = screen.label_style == LABEL_UNDER
        content = LARGE_INK_HEIGHT
        if screen.names:
            content += SMALL_INK_HEIGHT + INK_GAP
        if under:
            content += SMALL_INK_HEIGHT + INK_GAP
        top = frame_width + (DISPLAY_HEIGHT - 2 * frame_width - content) // 2
        if screen.names:
            self._draw_names(inset, top)
            top += SMALL_INK_HEIGHT + INK_GAP
        self._draw_matchup_label(top)
        self._draw_scores(inset, top)

    def _draw_scores(self, inset: int, top: int) -> None:
        """Draw the scores with their top lit row at `top`, bold or not."""
        screen = self.screen
        left_color, right_color = COLORS[screen.left], COLORS[screen.right]
        right_edge = DISPLAY_WIDTH - inset
        y = top - LARGE_INK_TOP
        left_text, right_text = str(screen.scores[0]), str(screen.scores[1])
        offsets = (0, 1) if screen.bold else (0,)
        if screen.label_style == LABEL_STACKED:
            left_x = inset - LARGE_INK_LEFT
            right_x = right_edge + LARGE_INK_RIGHT_PAD - offsets[-1]
            anchors = ((0.0, 0.0), (1.0, 0.0))
        else:
            left_x = DISPLAY_WIDTH // 4
            right_x = DISPLAY_WIDTH - left_x
            anchors = ((0.5, 0.0), (0.5, 0.0))
        for offset in offsets:
            position = (left_x + offset, y)
            self._add_text(left_text, 2, left_color, anchors[0], position)
            position = (right_x + offset, y)
            self._add_text(right_text, 2, right_color, anchors[1], position)

    def _draw_names(self, inset: int, top: int) -> None:
        """Draw the team names with their top lit row at `top`."""
        screen = self.screen
        y = top - SMALL_INK_TOP
        left_color = _scaled_color(COLORS[screen.left], screen.names_level)
        right_color = _scaled_color(COLORS[screen.right], screen.names_level)
        self._add_text("AWAY", 1, left_color, (0.0, 0.0), (inset, y))
        right = DISPLAY_WIDTH - inset + SMALL_INK_RIGHT_PAD
        self._add_text("HOME", 1, right_color, (1.0, 0.0), (right, y))

    def _draw_matchup_label(self, scores_top: int) -> None:
        """Draw the matchup label between or under scores whose top lit row is `scores_top`."""
        screen = self.screen
        center = DISPLAY_WIDTH // 2
        color = self._gender_color
        if screen.label_style == LABEL_STACKED:
            y = scores_top - SMALL_INK_TOP
            self._add_text(screen.label[:1], 1, color, (0.5, 0.0), (center, y))
            y += SMALL_INK_HEIGHT
            self._add_text(screen.label[1:], 1, color, (0.5, 0.0), (center, y))
        elif screen.label_style == LABEL_UNDER:
            y = scores_top + LARGE_INK_HEIGHT + INK_GAP - SMALL_INK_TOP
            self._add_text(screen.label, 1, color, (0.5, 0.0), (center, y))

    def _draw_large_digits(self) -> None:
        """Draw each score to fill its half, with optional names above."""
        screen = self.screen
        half = DISPLAY_WIDTH // 2
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
                position = (half_x + half_width // 2, top + height // 2)
                self._add_text(text, 2, COLORS[color_name], (0.5, 0.5), position)
                continue
            width = len(text) * DIGIT_WIDTH + (len(text) - 1) * DIGIT_GAP
            x = half_x + (half_width - width) // 2
            for digit in text:
                _draw_digit(self._bitmap, font, digit, x, top, height, index)
                x += DIGIT_WIDTH + DIGIT_GAP
        if screen.names:
            self._add_text("AWAY", 1, COLORS[screen.left], (0.0, 0.0), (margin, 0))
            right = (DISPLAY_WIDTH - 1, 0)
            self._add_text("HOME", 1, COLORS[screen.right], (1.0, 0.0), right)

    def _draw_gender(self) -> None:
        screen = self.screen
        bitmap = self._bitmap
        if screen.gender == GENDER_FRAME:
            self._frame, self._frame_distances = _frame_pixels(1)
        elif screen.gender == GENDER_THICK_FRAME:
            self._frame, self._frame_distances = _frame_pixels(THICK_FRAME_WIDTH)
        self._draw_frame(0 if screen.motion in _DASHED_MOTIONS else None)
        if screen.gender == GENDER_CORNERS:
            right = DISPLAY_WIDTH - CORNER_SIZE
            bottom = DISPLAY_HEIGHT - CORNER_SIZE
            for x, y in ((0, 0), (right, 0), (0, bottom), (right, bottom)):
                fill_rect(bitmap, x, y, CORNER_SIZE, CORNER_SIZE, _GENDER)
        elif screen.gender == GENDER_BAR:
            y = DISPLAY_HEIGHT - BAR_HEIGHT
            fill_rect(bitmap, 0, y, DISPLAY_WIDTH, BAR_HEIGHT, _GENDER)

    def _draw_frame(self, step: int | None) -> None:
        """Draw the frame solid when `step` is None, else dashed and shifted by `step`."""
        frame = self._frame
        distances = self._frame_distances
        period = DASH_LENGTH + DASH_GAP
        for i in range(len(frame)):
            lit = step is None or (distances[i] - step) % period < DASH_LENGTH
            self._bitmap[frame[i]] = _GENDER if lit else _GENDER_OFF

    def animate(self, elapsed: float) -> None:
        """Move the gender indicator to where it is `elapsed` seconds after the screen showed."""
        if self._current is not None:
            self._current.animate_wmp_frame()
            return
        motion = self.screen.motion
        if motion in {MOTION_MARCH, MOTION_MARCH_THEN_HOLD}:
            step = int(elapsed / MARCH_STEP_SECONDS) % (DASH_LENGTH + DASH_GAP)
            if motion == MOTION_MARCH_THEN_HOLD and elapsed >= WMP_FRAME_MARCH_SECONDS:
                step = 0
            if step != self._step:
                self._step = step
                self._draw_frame(step)
        elif motion == MOTION_BLINK:
            on = int(elapsed / BLINK_SECONDS) % 2 == 0
            self._palette[_GENDER] = (
                self._gender_color if on else BACKGROUNDS[self.screen.left_bg]
            )
        elif motion == MOTION_PULSE:
            step = int(elapsed / PULSE_STEP_SECONDS) % len(PULSE_LEVELS)
            self._palette[_GENDER] = self._pulse_colors[step]
