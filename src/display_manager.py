import time

import adafruit_miniqr
import displayio
import terminalio
from adafruit_display_text import label

from src.gender_manager import GenderManager
from src.protocols import MatrixPortalLike
from src.timing_indicator import TIMING_INDICATOR_PIXEL_COUNT

# Text element IDs
LEFT_TEAM = "left_team"
RIGHT_TEAM = "right_team"
LEFT_TEAM_SCORE = "left_team_score"
RIGHT_TEAM_SCORE = "right_team_score"
GENDER_MATCHUP = "gender_matchup"
GENDER_MATCHUP_COUNTER = "gender_matchup_counter"

# Color constants
MESSAGE_COLOR = 0xFFFF00
LEFT_TEAM_COLOR = 0xFFFF00  # AWAY team color (yellow)
RIGHT_TEAM_COLOR = 0x00FFFF  # HOME team color (cyan)
MMP_GENDER_MATCHUP_COLOR = 0xFFFFFF  # white
WMP_GENDER_MATCHUP_COLOR = 0xFF00FF  # magenta
WMP_FRAME_MARCH_SECONDS = 30.0
WMP_FRAME_MARCH_STEP_SECONDS = 0.1
FRAME_DASH_LENGTH = 5
FRAME_GAP_LENGTH = 3

# Font and scaling constants
TEAM_NAME_FONT_SCALE = 1
SCORE_FONT_SCALE = 2
GENDER_MATCHUP_FONT_SCALE = 1
FONT_TYPE = terminalio.FONT

# Display dimensions
DISPLAY_HEIGHT = 32
DISPLAY_WIDTH = 64
LEFT_BORDER_MARGIN_WIDTH = 2

# Position constants
TEAM_NAME_Y_POSITION = 0
SCORE_Y_POSITION = int(DISPLAY_HEIGHT * 0.25)
# Past the screen edge by the blank column at the right of each glyph
RIGHT_TEAM_SCORE_X_POSITION = DISPLAY_WIDTH + 1
GENDER_MATCHUP_X_POSITION = int(DISPLAY_WIDTH * 0.5) + 2
GENDER_MATCHUP_Y_POSITION = int(DISPLAY_HEIGHT * 0.35)
GENDER_MATCHUP_COUNTER_Y_OFFSET = 8
LEFT_JUSTIFY_ANCHOR_POINT = (0.0, 0.0)
MIDDLE_JUSTIFY_ANCHOR_POINT = (0.5, 0.0)
RIGHT_JUSTIFY_ANCHOR_POINT = (1.0, 0.0)

# Timing indicator constants
TIMING_INDICATOR_X_POSITION = (
    DISPLAY_WIDTH - LEFT_BORDER_MARGIN_WIDTH - TIMING_INDICATOR_PIXEL_COUNT
)
# The row above the frame's bottom edge
TIMING_INDICATOR_Y_POSITION = DISPLAY_HEIGHT - 2
TIMING_INDICATOR_COLOR = 0xFFFFFF

# QR code constants
QR_CODE_LIGHT_COLOR = 0x808080
QR_CODE_QUIET_ZONE_WIDTH = 2


# (element ID, initial text, scale, color, anchor point, anchored position)
_ANCHORED_LABELS = (
    (
        LEFT_TEAM,
        "",
        TEAM_NAME_FONT_SCALE,
        LEFT_TEAM_COLOR,
        LEFT_JUSTIFY_ANCHOR_POINT,
        (LEFT_BORDER_MARGIN_WIDTH, TEAM_NAME_Y_POSITION),
    ),
    (
        RIGHT_TEAM,
        "",
        TEAM_NAME_FONT_SCALE,
        RIGHT_TEAM_COLOR,
        RIGHT_JUSTIFY_ANCHOR_POINT,
        (DISPLAY_WIDTH - 1, TEAM_NAME_Y_POSITION),
    ),
    (
        LEFT_TEAM_SCORE,
        "",
        SCORE_FONT_SCALE,
        LEFT_TEAM_COLOR,
        LEFT_JUSTIFY_ANCHOR_POINT,
        (LEFT_BORDER_MARGIN_WIDTH, SCORE_Y_POSITION),
    ),
    (
        RIGHT_TEAM_SCORE,
        "",
        SCORE_FONT_SCALE,
        RIGHT_TEAM_COLOR,
        RIGHT_JUSTIFY_ANCHOR_POINT,
        (RIGHT_TEAM_SCORE_X_POSITION, SCORE_Y_POSITION),
    ),
    (
        GENDER_MATCHUP,
        " ",
        GENDER_MATCHUP_FONT_SCALE,
        WMP_GENDER_MATCHUP_COLOR,
        MIDDLE_JUSTIFY_ANCHOR_POINT,
        (GENDER_MATCHUP_X_POSITION, GENDER_MATCHUP_Y_POSITION),
    ),
    (
        GENDER_MATCHUP_COUNTER,
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


def make_qr_matrix(text: str) -> adafruit_miniqr.QRBitMatrix:
    """Return the QR code modules for `text`, truthy where a module is dark."""
    qr = adafruit_miniqr.QRCode()
    qr.add_data(text.encode())
    qr.make()
    matrix = qr.matrix
    assert matrix is not None
    return matrix


class DisplayManager:
    """Lays out the scoreboard and updates what it shows."""

    def __init__(self, matrixportal: MatrixPortalLike):
        self._labels: dict[str, label.Label] = {}
        self._main_group = displayio.Group()

        for element_id, text, scale, color, anchor_point, position in _ANCHORED_LABELS:
            self._add_label(
                element_id,
                label.Label(
                    FONT_TYPE,
                    text=text,
                    scale=scale,
                    color=color,
                    anchor_point=anchor_point,
                    anchored_position=position,
                ),
            )

        self._setup_frames()
        self._setup_timing_indicator()
        self._setup_message()
        self._setup_qr_code()
        matrixportal.display.root_group = self._main_group

    def _add_label(self, element_id: str, label_obj: label.Label) -> None:
        self._labels[element_id] = label_obj
        self._main_group.append(label_obj)

    def set_team_names(self, left_team: str, right_team: str) -> None:
        self._labels[LEFT_TEAM].text = left_team
        self._labels[RIGHT_TEAM].text = right_team

    def set_scores(self, left_score: int, right_score: int) -> None:
        self._labels[LEFT_TEAM_SCORE].text = str(left_score)
        self._labels[RIGHT_TEAM_SCORE].text = str(right_score)

    def set_gender_matchup(self, gender: str, count: int) -> None:
        """Show the gender matchup and frame the screen, both colored by gender.

        The WMP frame's dashes hold still.
        """
        is_wmp = gender == GenderManager.GENDER_WMP
        color = WMP_GENDER_MATCHUP_COLOR if is_wmp else MMP_GENDER_MATCHUP_COLOR
        self._wmp_frame.hidden = not is_wmp
        self._mmp_frame.hidden = is_wmp
        self._wmp_frame_march_start = -WMP_FRAME_MARCH_SECONDS
        for element_id, text in (
            (GENDER_MATCHUP, gender),
            (GENDER_MATCHUP_COUNTER, str(count)),
        ):
            self._labels[element_id].text = text
            self._labels[element_id].color = color

    def _setup_message(self) -> None:
        """Initialize a hidden, full-screen message that covers the scoreboard."""
        palette = displayio.Palette(1)
        palette[0] = 0x000000
        self._message_label = label.Label(
            FONT_TYPE,
            text=" ",
            color=MESSAGE_COLOR,
            anchor_point=(0.5, 0.5),
            anchored_position=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2),
        )
        self._message = displayio.Group()
        self._message.append(
            displayio.TileGrid(
                displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1), pixel_shader=palette
            )
        )
        self._message.append(self._message_label)
        self._message.hidden = True
        self._main_group.append(self._message)

    def show_message(self, text: str) -> None:
        """Cover the scoreboard with centered text."""
        self._message_label.text = text
        self._message.hidden = False

    def hide_message(self) -> None:
        self._message.hidden = True

    def _setup_frames(self) -> None:
        """Initialize hidden WMP and MMP frames around the edge of the screen."""
        right, bottom = DISPLAY_WIDTH - 1, DISPLAY_HEIGHT - 1
        self._frame_pixels = (
            [(x, 0) for x in range(right)]
            + [(right, y) for y in range(bottom)]
            + [(x, bottom) for x in range(right, 0, -1)]
            + [(0, y) for y in range(bottom, 0, -1)]
        )
        self._wmp_frame = self._add_frame(WMP_GENDER_MATCHUP_COLOR)
        self._wmp_frame_march_start = -WMP_FRAME_MARCH_SECONDS
        self._wmp_frame_offset = -1
        self.animate_wmp_frame()
        self._mmp_frame = self._add_frame(MMP_GENDER_MATCHUP_COLOR)
        self._draw_mmp_frame(include_bottom=True)

    def _add_frame(self, color: int) -> displayio.TileGrid:
        """Add a hidden, full-screen TileGrid that lights its pixels in `color`."""
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = color
        palette.make_transparent(0)
        tile_grid = displayio.TileGrid(
            displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 2), pixel_shader=palette
        )
        tile_grid.hidden = True
        self._main_group.append(tile_grid)
        return tile_grid

    def _draw_frame(self, bitmap: displayio.Bitmap, dash_offset: int) -> None:
        """Draw the frame as dashes shifted along the edge by `dash_offset`.

        Runs without allocating, so marching dashes don't trigger garbage
        collection pauses.
        """
        period = FRAME_DASH_LENGTH + FRAME_GAP_LENGTH
        pixels = self._frame_pixels
        for i in range(len(pixels)):
            lit = (i - dash_offset) % period < FRAME_DASH_LENGTH
            bitmap[pixels[i]] = 1 if lit else 0

    def _draw_mmp_frame(self, include_bottom: bool) -> None:
        """Draw the MMP frame, leaving its bottom edge dark unless `include_bottom`."""
        bitmap = self._mmp_frame.bitmap
        self._draw_frame(bitmap, 0)
        if not include_bottom:
            for x in range(DISPLAY_WIDTH):
                bitmap[x, DISPLAY_HEIGHT - 1] = 0

    def march_wmp_frame(self) -> None:
        """March dashes around the WMP frame for WMP_FRAME_MARCH_SECONDS."""
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
        """Initialize the timing indicator bar just above the frame's bottom edge."""
        self._timing_indicator_bitmap = displayio.Bitmap(
            TIMING_INDICATOR_PIXEL_COUNT, 1, 2
        )
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = TIMING_INDICATOR_COLOR
        palette.make_transparent(0)
        tile_grid = displayio.TileGrid(
            self._timing_indicator_bitmap,
            pixel_shader=palette,
            x=TIMING_INDICATOR_X_POSITION,
            y=TIMING_INDICATOR_Y_POSITION,
        )
        self._main_group.append(tile_grid)

    def update_timing_indicator(self, count: int) -> None:
        """Light the right-most `count` pixels of the timing indicator.

        The MMP frame's bottom edge shows only while the indicator is empty.

        :param count: Number of pixels to light (0 to TIMING_INDICATOR_PIXEL_COUNT)
        """
        count = max(0, min(count, TIMING_INDICATOR_PIXEL_COUNT))
        self._draw_mmp_frame(include_bottom=count == 0)
        first_lit = TIMING_INDICATOR_PIXEL_COUNT - count
        for i in range(TIMING_INDICATOR_PIXEL_COUNT):
            self._timing_indicator_bitmap[i, 0] = 1 if i >= first_lit else 0

    def _setup_qr_code(self) -> None:
        """Initialize a hidden, full-screen QR code that covers everything else."""
        palette = displayio.Palette(2)
        palette[0] = 0x000000
        palette[1] = QR_CODE_LIGHT_COLOR
        self._qr_code = displayio.TileGrid(
            displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 2), pixel_shader=palette
        )
        self._qr_code.hidden = True
        self._main_group.append(self._qr_code)

    @property
    def qr_code_shown(self) -> bool:
        return not self._qr_code.hidden

    def show_qr_code(self, text: str) -> None:
        """Cover the screen with a centered QR code for `text`."""
        matrix = make_qr_matrix(text)
        left = (DISPLAY_WIDTH - matrix.width) // 2
        top = (DISPLAY_HEIGHT - matrix.height) // 2
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
                bitmap[x, y] = 1 if in_quiet_zone and not dark else 0
        self._qr_code.hidden = False

    def hide_qr_code(self) -> None:
        self._qr_code.hidden = True
