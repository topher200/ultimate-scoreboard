import time

import displayio
import terminalio
from adafruit_display_text import label

from src.gender_manager import GenderManager
from src.lab_font import DIGITS_3X5, draw_glyph
from src.proportional_font import ProportionalFont
from src.protocols import MatrixPortalLike
from src.qr_matrix import make_qr_matrix
from src.timing_indicator import TIMING_INDICATOR_PIXEL_COUNT

# Text element IDs
LEFT_TEAM = "left_team"
RIGHT_TEAM = "right_team"
LEFT_TEAM_SCORE = "left_team_score"
RIGHT_TEAM_SCORE = "right_team_score"
# Second copies of the scores, one column to the right, which make them bold
LEFT_TEAM_SCORE_BOLD = "left_team_score_bold"
RIGHT_TEAM_SCORE_BOLD = "right_team_score_bold"
GENDER_MATCHUP = "gender_matchup"
GENDER_MATCHUP_COUNTER = "gender_matchup_counter"

# Color constants
WIFI_ICON_COLOR = 0x00FFFF
WIFI_SEARCH_TEXT_COLOR = 0xFFFFFF
LEFT_TEAM_COLOR = 0xFFFF00  # AWAY team color (yellow)
RIGHT_TEAM_COLOR = 0xFFFFFF  # HOME team color (white)
# Team names at 2/3 brightness, so the scores stand out
LEFT_TEAM_NAME_COLOR = 0xAAAA00
RIGHT_TEAM_NAME_COLOR = 0xAAAAAA
MMP_GENDER_MATCHUP_COLOR = 0xFF00FF  # magenta
WMP_GENDER_MATCHUP_COLOR = 0x00FFFF  # cyan
WMP_FRAME_MARCH_SECONDS = 30.0
WMP_FRAME_MARCH_STEP_SECONDS = 0.1
FRAME_WIDTH = 3
FRAME_DASH_LENGTH = 5
FRAME_GAP_LENGTH = 3

# Font and scaling constants
TEAM_NAME_FONT_SCALE = 1
SCORE_FONT_SCALE = 2
GENDER_MATCHUP_FONT_SCALE = 1
FONT_TYPE = terminalio.FONT
TEAM_NAME_FONT = ProportionalFont(terminalio.FONT)

# Display dimensions
DISPLAY_HEIGHT = 32
DISPLAY_WIDTH = 64
# Columns between the screen edge and the text, one more than the frame
TEXT_INSET = FRAME_WIDTH + 1

# Position constants. The terminal font lights its first row 2 rows below a
# label's top at scale 1 and 4 rows below at scale 2, and leaves blank columns
# at the sides of each glyph.
# Names light rows 3-10
TEAM_NAME_Y_POSITION = 1
# Scores light rows 12-27
SCORE_Y_POSITION = 8
LEFT_TEAM_SCORE_X_POSITION = TEXT_INSET
RIGHT_TEAM_SCORE_X_POSITION = DISPLAY_WIDTH - TEXT_INSET + 2
RIGHT_TEAM_NAME_X_POSITION = DISPLAY_WIDTH - TEXT_INSET + 1
GENDER_MATCHUP_X_POSITION = DISPLAY_WIDTH // 2
GENDER_MATCHUP_Y_POSITION = 10
GENDER_MATCHUP_COUNTER_Y_OFFSET = 8
LEFT_JUSTIFY_ANCHOR_POINT = (0.0, 0.0)
MIDDLE_JUSTIFY_ANCHOR_POINT = (0.5, 0.0)
RIGHT_JUSTIFY_ANCHOR_POINT = (1.0, 0.0)

# Timing indicator constants
TIMING_INDICATOR_X_POSITION = DISPLAY_WIDTH - TEXT_INSET - TIMING_INDICATOR_PIXEL_COUNT
# The row between the scores and the frame's bottom edge
TIMING_INDICATOR_Y_POSITION = DISPLAY_HEIGHT - FRAME_WIDTH - 1
# The row for an MMP point, which has no frame
MMP_TIMING_INDICATOR_Y_POSITION = DISPLAY_HEIGHT - 2
TIMING_INDICATOR_COLOR = 0xFFFFFF

# Update screen constants
UPDATE_NOTICE_TEXT = "Updating"
UPDATE_NOTICE_TEXT_COLOR = 0xFFFFFF

# Wi-Fi search screen constants
WIFI_SEARCH_TEXT = "Searching"
WIFI_ICON_Y_POSITION = 3
WIFI_SEARCH_TEXT_Y_POSITION = 22
WIFI_ICON = (
    "..XXXXXXX..",
    ".X.......X.",
    "X..XXXXX..X",
    "..X.....X..",
    ".X..XXX..X.",
    "...X...X...",
    "...........",
    ".....X.....",
)

# QR code constants
QR_CODE_LIGHT_COLOR = 0x808080
QR_CODE_QUIET_ZONE_WIDTH = 2
# Beside its address, the code sits at the left edge, with its quiet zone
# starting at column 0
QR_CODE_LEFT = QR_CODE_QUIET_ZONE_WIDTH
# Palette indexes of the QR code screen
QR_CODE_DARK_INDEX = 0
QR_CODE_LIGHT_INDEX = 1
ADDRESS_TEXT_INDEX = 2

# Address beside the QR code, for typing in when the code does not scan
ADDRESS_TEXT_COLOR = 0xFFFFFF
# Blank pixels between the quiet zone and the address
ADDRESS_GAP = 1
ADDRESS_LETTER_SPACING = 1
ADDRESS_LINE_SPACING = 2
ADDRESS_GLYPH_HEIGHT = 5
# 3x5 digits, plus a one-column dot and colon
ADDRESS_GLYPHS = dict(DIGITS_3X5)
ADDRESS_GLYPHS["."] = ("0", "0", "0", "0", "1")
ADDRESS_GLYPHS[":"] = ("0", "1", "0", "1", "0")


# (element ID, font, initial text, scale, color, anchor point, anchored position)
_ANCHORED_LABELS = (
    (
        LEFT_TEAM,
        TEAM_NAME_FONT,
        "",
        TEAM_NAME_FONT_SCALE,
        LEFT_TEAM_NAME_COLOR,
        LEFT_JUSTIFY_ANCHOR_POINT,
        (TEXT_INSET, TEAM_NAME_Y_POSITION),
    ),
    (
        RIGHT_TEAM,
        TEAM_NAME_FONT,
        "",
        TEAM_NAME_FONT_SCALE,
        RIGHT_TEAM_NAME_COLOR,
        RIGHT_JUSTIFY_ANCHOR_POINT,
        (RIGHT_TEAM_NAME_X_POSITION, TEAM_NAME_Y_POSITION),
    ),
    (
        LEFT_TEAM_SCORE,
        FONT_TYPE,
        "",
        SCORE_FONT_SCALE,
        LEFT_TEAM_COLOR,
        LEFT_JUSTIFY_ANCHOR_POINT,
        (LEFT_TEAM_SCORE_X_POSITION, SCORE_Y_POSITION),
    ),
    (
        LEFT_TEAM_SCORE_BOLD,
        FONT_TYPE,
        "",
        SCORE_FONT_SCALE,
        LEFT_TEAM_COLOR,
        LEFT_JUSTIFY_ANCHOR_POINT,
        (LEFT_TEAM_SCORE_X_POSITION + 1, SCORE_Y_POSITION),
    ),
    (
        RIGHT_TEAM_SCORE,
        FONT_TYPE,
        "",
        SCORE_FONT_SCALE,
        RIGHT_TEAM_COLOR,
        RIGHT_JUSTIFY_ANCHOR_POINT,
        (RIGHT_TEAM_SCORE_X_POSITION - 1, SCORE_Y_POSITION),
    ),
    (
        RIGHT_TEAM_SCORE_BOLD,
        FONT_TYPE,
        "",
        SCORE_FONT_SCALE,
        RIGHT_TEAM_COLOR,
        RIGHT_JUSTIFY_ANCHOR_POINT,
        (RIGHT_TEAM_SCORE_X_POSITION, SCORE_Y_POSITION),
    ),
    (
        GENDER_MATCHUP,
        FONT_TYPE,
        " ",
        GENDER_MATCHUP_FONT_SCALE,
        WMP_GENDER_MATCHUP_COLOR,
        MIDDLE_JUSTIFY_ANCHOR_POINT,
        (GENDER_MATCHUP_X_POSITION, GENDER_MATCHUP_Y_POSITION),
    ),
    (
        GENDER_MATCHUP_COUNTER,
        FONT_TYPE,
        " ",
        GENDER_MATCHUP_FONT_SCALE,
        WMP_GENDER_MATCHUP_COLOR,
        MIDDLE_JUSTIFY_ANCHOR_POINT,
        (
            GENDER_MATCHUP_X_POSITION,
            GENDER_MATCHUP_Y_POSITION + GENDER_MATCHUP_COUNTER_Y_OFFSET,
        ),
    ),
)


def frame_pixels(width: int) -> tuple[list, list]:
    """Return the (x, y) pixels of a frame `width` thick around the screen, and
    the distance of each along the outer edge, clockwise from the top-left corner."""
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


def lit_pixels(text: label.Label) -> set:
    """Return the (x, y) screen pixels that `text` lights, at scale 1."""
    pixels = set()
    group = text._local_group
    for i in range(len(group)):
        face = group[i]
        if not isinstance(face, displayio.TileGrid):
            continue
        bitmap = face.bitmap
        width, height = face.tile_width, face.tile_height
        tile = face[0]
        tile_x = tile % (bitmap.width // width) * width
        tile_y = tile // (bitmap.width // width) * height
        for y in range(height):
            for x in range(width):
                if bitmap[tile_x + x, tile_y + y]:
                    pixels.add((text.x + face.x + x, text.y + face.y + y))
    return pixels


def address_line(url: str) -> str:
    """Return the host and port of `url`: "HTTP://1.2.3.4:81/" gives "1.2.3.4:81"."""
    return url.split("://", 1)[-1].rstrip("/")


def address_lines(url: str) -> list[str]:
    """Split the host and port of `url` into the lines shown beside its QR code.

    An IPv4 address shows two parts per line, with the port on its own line:
    "HTTP://10.115.170.193:81" shows "10.115.", "170.193" and ":81".
    """
    address = address_line(url)
    host, separator, port = address.rpartition(":")
    if not separator:
        host, port = address, ""
    parts = host.split(".")
    if len(parts) == 4:
        lines = [".".join(parts[:2]) + ".", ".".join(parts[2:])]
    else:
        lines = [host]
    if port:
        lines.append(":" + port)
    return lines


def address_text_width(text: str) -> int:
    """Return the pixels that `text` spans in the address font."""
    glyphs = [ADDRESS_GLYPHS[char] for char in text if char in ADDRESS_GLYPHS]
    if not glyphs:
        return 0
    widths = sum(len(glyph[0]) for glyph in glyphs)
    return widths + ADDRESS_LETTER_SPACING * (len(glyphs) - 1)


def address_fits_below(matrix, url: str) -> bool:
    """True when the address of `url` fits on one line below `matrix`."""
    code_height = matrix.height + 2 * QR_CODE_QUIET_ZONE_WIDTH
    return (
        address_text_width(address_line(url)) <= DISPLAY_WIDTH
        and code_height + ADDRESS_GAP + ADDRESS_GLYPH_HEIGHT <= DISPLAY_HEIGHT
    )


def qr_code_origin(matrix, url: str) -> tuple[int, int]:
    """Return the column and row of the top-left module of `url`'s QR code.

    With the address below, the code is centered at the top. Otherwise it sits
    at the left edge, centered vertically.
    """
    if address_fits_below(matrix, url):
        return (DISPLAY_WIDTH - matrix.width) // 2, QR_CODE_QUIET_ZONE_WIDTH
    return QR_CODE_LEFT, (DISPLAY_HEIGHT - matrix.height) // 2


class DisplayManager:
    """Lays out the scoreboard and updates what it shows."""

    def __init__(self, matrixportal: MatrixPortalLike):
        self._labels: dict[str, label.Label] = {}
        self._show_wmp_frame = True
        self._march_wmp_frame_enabled = True
        self._is_wmp = False
        self._main_group = displayio.Group()

        for (
            element_id,
            font,
            text,
            scale,
            color,
            anchor_point,
            position,
        ) in _ANCHORED_LABELS:
            self._add_label(
                element_id,
                label.Label(
                    font,
                    text=text,
                    scale=scale,
                    color=color,
                    anchor_point=anchor_point,
                    anchored_position=position,
                ),
            )

        self._setup_frames()
        self._setup_timing_indicator()
        self._setup_wifi_search()
        self._setup_qr_code()
        self._setup_update_notice()
        matrixportal.display.root_group = self._main_group

    def _add_label(self, element_id: str, label_obj: label.Label) -> None:
        self._labels[element_id] = label_obj
        self._main_group.append(label_obj)

    def set_team_names(self, left_team: str, right_team: str) -> None:
        self._labels[LEFT_TEAM].text = left_team
        self._labels[RIGHT_TEAM].text = right_team
        self._clear_frame_around_names()

    def set_scores(self, left_score: int, right_score: int) -> None:
        for element_id in (LEFT_TEAM_SCORE, LEFT_TEAM_SCORE_BOLD):
            self._labels[element_id].text = str(left_score)
        for element_id in (RIGHT_TEAM_SCORE, RIGHT_TEAM_SCORE_BOLD):
            self._labels[element_id].text = str(right_score)

    def set_gender_matchup(self, gender: str, count: int) -> None:
        """Show the gender's first letter over the count, colored by gender.

        A WMP point also frames the screen, with its dashes held still. An MMP
        point moves the timing dots down into the frame's space.
        """
        is_wmp = gender == GenderManager.GENDER_WMP
        color = WMP_GENDER_MATCHUP_COLOR if is_wmp else MMP_GENDER_MATCHUP_COLOR
        self._is_wmp = is_wmp
        self._update_frame_visibility()
        self._timing_indicator.y = (
            TIMING_INDICATOR_Y_POSITION if is_wmp else MMP_TIMING_INDICATOR_Y_POSITION
        )
        self._wmp_frame_march_start = -WMP_FRAME_MARCH_SECONDS
        for element_id, text in (
            (GENDER_MATCHUP, gender[:1]),
            (GENDER_MATCHUP_COUNTER, str(count)),
        ):
            self._labels[element_id].text = text
            self._labels[element_id].color = color

    def set_frame_options(self, show_wmp_frame: bool, march_wmp_frame: bool) -> None:
        """Choose whether the WMP frame shows and whether its dashes march."""
        self._show_wmp_frame = show_wmp_frame
        self._march_wmp_frame_enabled = march_wmp_frame
        if not march_wmp_frame:
            self._wmp_frame_march_start = -WMP_FRAME_MARCH_SECONDS
        self._update_frame_visibility()

    def _update_frame_visibility(self) -> None:
        self._wmp_frame.hidden = not (self._show_wmp_frame and self._is_wmp)

    def _setup_wifi_search(self) -> None:
        """Initialize a hidden, full-screen Wi-Fi icon and "Searching" that cover the scoreboard."""
        background_palette = displayio.Palette(1)
        background_palette[0] = 0x000000
        icon_bitmap = displayio.Bitmap(len(WIFI_ICON[0]), len(WIFI_ICON), 2)
        for y, row in enumerate(WIFI_ICON):
            for x, char in enumerate(row):
                icon_bitmap[x, y] = 1 if char == "X" else 0
        icon_palette = displayio.Palette(2)
        icon_palette[0] = 0x000000
        icon_palette[1] = WIFI_ICON_COLOR
        icon_palette.make_transparent(0)

        self._wifi_search = displayio.Group()
        self._wifi_search.append(
            displayio.TileGrid(
                displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1),
                pixel_shader=background_palette,
            )
        )
        self._wifi_search.append(
            displayio.TileGrid(
                icon_bitmap,
                pixel_shader=icon_palette,
                x=(DISPLAY_WIDTH - len(WIFI_ICON[0])) // 2,
                y=WIFI_ICON_Y_POSITION,
            )
        )
        self._wifi_search.append(
            label.Label(
                FONT_TYPE,
                text=WIFI_SEARCH_TEXT,
                color=WIFI_SEARCH_TEXT_COLOR,
                anchor_point=(0.5, 0.5),
                anchored_position=(DISPLAY_WIDTH // 2, WIFI_SEARCH_TEXT_Y_POSITION),
            )
        )
        self._wifi_search.hidden = True
        self._main_group.append(self._wifi_search)

    @property
    def wifi_search_shown(self) -> bool:
        return not self._wifi_search.hidden

    def show_wifi_search(self) -> None:
        self._wifi_search.hidden = False

    def hide_wifi_search(self) -> None:
        self._wifi_search.hidden = True

    def _setup_update_notice(self) -> None:
        """Initialize a hidden, full-screen "Updating" that covers everything else."""
        background_palette = displayio.Palette(1)
        background_palette[0] = 0x000000
        self._update_notice = displayio.Group()
        self._update_notice.append(
            displayio.TileGrid(
                displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1),
                pixel_shader=background_palette,
            )
        )
        self._update_notice.append(
            label.Label(
                FONT_TYPE,
                text=UPDATE_NOTICE_TEXT,
                color=UPDATE_NOTICE_TEXT_COLOR,
                anchor_point=(0.5, 0.5),
                anchored_position=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2),
            )
        )
        self._update_notice.hidden = True
        self._main_group.append(self._update_notice)

    @property
    def update_notice_shown(self) -> bool:
        return not self._update_notice.hidden

    def show_update_notice(self) -> None:
        self._update_notice.hidden = False

    def hide_update_notice(self) -> None:
        self._update_notice.hidden = True

    def _setup_frames(self) -> None:
        """Initialize a hidden WMP frame around the edge of the screen."""
        self._all_frame_pixels, self._all_frame_distances = frame_pixels(FRAME_WIDTH)
        self._frame_pixels = self._all_frame_pixels
        self._frame_distances = self._all_frame_distances
        self._frame_clears_names = True
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = WMP_GENDER_MATCHUP_COLOR
        palette.make_transparent(0)
        self._wmp_frame = displayio.TileGrid(
            displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 2), pixel_shader=palette
        )
        self._wmp_frame.hidden = True
        self._main_group.append(self._wmp_frame)
        self._wmp_frame_march_start = -WMP_FRAME_MARCH_SECONDS
        self._wmp_frame_offset = -1
        self.animate_wmp_frame()

    def _draw_frame(self, bitmap: displayio.Bitmap, dash_offset: int) -> None:
        """Draw the frame as dashes shifted along the edge by `dash_offset`.

        Runs without allocating, so marching dashes don't trigger garbage
        collection pauses.
        """
        period = FRAME_DASH_LENGTH + FRAME_GAP_LENGTH
        pixels = self._frame_pixels
        distances = self._frame_distances
        for i in range(len(pixels)):
            lit = (distances[i] - dash_offset) % period < FRAME_DASH_LENGTH
            bitmap[pixels[i]] = 1 if lit else 0

    def _clear_frame_around_names(self) -> None:
        """Keep the WMP frame dark within 1 px of each team name pixel."""
        near = set()
        if self._frame_clears_names:
            inner = range(FRAME_WIDTH + 1, DISPLAY_WIDTH - FRAME_WIDTH - 1)
            for element_id in (LEFT_TEAM, RIGHT_TEAM):
                for x, y in lit_pixels(self._labels[element_id]):
                    if (
                        x in inner
                        and FRAME_WIDTH < y < DISPLAY_HEIGHT - FRAME_WIDTH - 1
                    ):
                        continue
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            near.add((x + dx, y + dy))
        bitmap = self._wmp_frame.bitmap
        pixels = []
        distances = []
        for i, pixel in enumerate(self._all_frame_pixels):
            if pixel in near:
                bitmap[pixel] = 0
            else:
                pixels.append(pixel)
                distances.append(self._all_frame_distances[i])
        self._frame_pixels = pixels
        self._frame_distances = distances
        self._draw_frame(bitmap, self._wmp_frame_offset)

    def march_wmp_frame(self) -> None:
        """March dashes around the WMP frame for WMP_FRAME_MARCH_SECONDS, if enabled."""
        if not self._march_wmp_frame_enabled:
            return
        self._wmp_frame_march_start = time.monotonic()

    def animate_wmp_frame(self) -> None:
        """Advance the WMP frame's dashes while they march, then hold them still."""
        elapsed = time.monotonic() - self._wmp_frame_march_start
        offset = (
            int(elapsed / WMP_FRAME_MARCH_STEP_SECONDS)
            % (FRAME_DASH_LENGTH + FRAME_GAP_LENGTH)
            if elapsed < WMP_FRAME_MARCH_SECONDS
            else 0
        )
        if offset == self._wmp_frame_offset:
            return
        self._wmp_frame_offset = offset
        self._draw_frame(self._wmp_frame.bitmap, offset)

    def _setup_timing_indicator(self) -> None:
        """Initialize the timing indicator bar just inside the frame's bottom edge."""
        self._timing_indicator_bitmap = displayio.Bitmap(
            TIMING_INDICATOR_PIXEL_COUNT, 1, 2
        )
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = TIMING_INDICATOR_COLOR
        palette.make_transparent(0)
        self._timing_indicator = displayio.TileGrid(
            self._timing_indicator_bitmap,
            pixel_shader=palette,
            x=TIMING_INDICATOR_X_POSITION,
            y=TIMING_INDICATOR_Y_POSITION,
        )
        self._main_group.append(self._timing_indicator)

    def update_timing_indicator(self, count: int) -> None:
        """Light the right-most `count` pixels of the timing indicator.

        :param count: Number of pixels to light (0 to TIMING_INDICATOR_PIXEL_COUNT)
        """
        count = max(0, min(count, TIMING_INDICATOR_PIXEL_COUNT))
        first_lit = TIMING_INDICATOR_PIXEL_COUNT - count
        for i in range(TIMING_INDICATOR_PIXEL_COUNT):
            self._timing_indicator_bitmap[i, 0] = 1 if i >= first_lit else 0

    def _setup_qr_code(self) -> None:
        """Initialize a hidden, full-screen QR code that covers everything else."""
        palette = displayio.Palette(3)
        palette[QR_CODE_DARK_INDEX] = 0x000000
        palette[QR_CODE_LIGHT_INDEX] = QR_CODE_LIGHT_COLOR
        palette[ADDRESS_TEXT_INDEX] = ADDRESS_TEXT_COLOR
        self._qr_code = displayio.TileGrid(
            displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 3), pixel_shader=palette
        )
        self._qr_code.hidden = True
        self._main_group.append(self._qr_code)

    @property
    def qr_code_shown(self) -> bool:
        return not self._qr_code.hidden

    def show_qr_code(self, url: str) -> None:
        """Cover the screen with a QR code for `url` and its address as text.

        The address goes on one line below the code when it fits, and beside
        the code otherwise.
        """
        matrix = make_qr_matrix(url)
        left, top = qr_code_origin(matrix, url)
        margin = QR_CODE_QUIET_ZONE_WIDTH
        bitmap = self._qr_code.bitmap
        for y in range(DISPLAY_HEIGHT):
            qr_y = y - top
            for x in range(DISPLAY_WIDTH):
                qr_x = x - left
                in_quiet_zone = (
                    -margin <= qr_x < matrix.width + margin
                    and -margin <= qr_y < matrix.height + margin
                )
                in_code = 0 <= qr_x < matrix.width and 0 <= qr_y < matrix.height
                dark = in_code and matrix[qr_x, qr_y]
                bitmap[x, y] = (
                    QR_CODE_LIGHT_INDEX
                    if in_quiet_zone and not dark
                    else QR_CODE_DARK_INDEX
                )
        if address_fits_below(matrix, url):
            text_top = top + matrix.height + margin + ADDRESS_GAP
            self._draw_address(
                [address_line(url)], 0, text_top, DISPLAY_WIDTH, ADDRESS_GLYPH_HEIGHT
            )
        else:
            text_left = left + matrix.width + margin + ADDRESS_GAP
            self._draw_address(
                address_lines(url),
                text_left,
                0,
                DISPLAY_WIDTH - text_left,
                DISPLAY_HEIGHT,
            )
        self._qr_code.hidden = False

    def _draw_address(
        self, lines: list[str], left: int, top: int, width: int, height: int
    ) -> None:
        """Draw `lines` centered in the area at `left`, `top` of `width` by
        `height` pixels."""
        bitmap = self._qr_code.bitmap
        block_height = len(lines) * (ADDRESS_GLYPH_HEIGHT + ADDRESS_LINE_SPACING)
        y = top + (height - block_height + ADDRESS_LINE_SPACING) // 2
        for line in lines:
            x = left + (width - address_text_width(line)) // 2
            for char in line:
                glyph = ADDRESS_GLYPHS.get(char)
                if glyph is None:
                    continue
                draw_glyph(bitmap, glyph, x, y, 1, 1, ADDRESS_TEXT_INDEX)
                x += len(glyph[0]) + ADDRESS_LETTER_SPACING
            y += ADDRESS_GLYPH_HEIGHT + ADDRESS_LINE_SPACING

    def hide_qr_code(self) -> None:
        self._qr_code.hidden = True
