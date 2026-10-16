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
CONNECTING = "connecting"

# Color constants
CONNECTING_COLOR = 0xFFFF00
LEFT_TEAM_COLOR = 0xFFFF00  # AWAY team color (yellow)
RIGHT_TEAM_COLOR = 0x00FFFF  # HOME team color (cyan)
MMP_GENDER_MATCHUP_COLOR = 0xFFD700  # gold
WMP_GENDER_MATCHUP_COLOR = 0xFF80C0  # light pink

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
GENDER_MATCHUP_X_POSITION = int(DISPLAY_WIDTH * 0.5) + 2
GENDER_MATCHUP_Y_POSITION = int(DISPLAY_HEIGHT * 0.35)
LEFT_JUSTIFY_ANCHOR_POINT = (0.0, 0.0)
MIDDLE_JUSTIFY_ANCHOR_POINT = (0.5, 0.0)
RIGHT_JUSTIFY_ANCHOR_POINT = (1.0, 0.0)

# Timing indicator constants
TIMING_INDICATOR_X_POSITION = (
    DISPLAY_WIDTH - LEFT_BORDER_MARGIN_WIDTH - TIMING_INDICATOR_PIXEL_COUNT
)
TIMING_INDICATOR_Y_POSITION = DISPLAY_HEIGHT - 1
TIMING_INDICATOR_COLOR = 0xFFFFFF


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
        (DISPLAY_WIDTH, TEAM_NAME_Y_POSITION),
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
        (DISPLAY_WIDTH, SCORE_Y_POSITION),
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
        (GENDER_MATCHUP_X_POSITION, GENDER_MATCHUP_Y_POSITION + 10),
    ),
)


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

        connecting_label = label.Label(FONT_TYPE, text=" ", color=CONNECTING_COLOR)
        connecting_label.x = DISPLAY_WIDTH - 5
        connecting_label.y = DISPLAY_HEIGHT - 5
        self._add_label(CONNECTING, connecting_label)

        self._setup_timing_indicator()
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
        """Show the gender matchup, colored by gender."""
        color = (
            MMP_GENDER_MATCHUP_COLOR
            if gender == GenderManager.GENDER_MMP
            else WMP_GENDER_MATCHUP_COLOR
        )
        for element_id, text in (
            (GENDER_MATCHUP, gender),
            (GENDER_MATCHUP_COUNTER, str(count)),
        ):
            self._labels[element_id].text = text
            self._labels[element_id].color = color

    def show_connecting(self, show: bool) -> None:
        """Show or hide the connecting indicator."""
        self._labels[CONNECTING].text = "." if show else " "

    def _setup_timing_indicator(self) -> None:
        """Initialize the timing indicator bar on the bottom row of the screen."""
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

        :param count: Number of pixels to light (0 to TIMING_INDICATOR_PIXEL_COUNT)
        """
        count = max(0, min(count, TIMING_INDICATOR_PIXEL_COUNT))
        first_lit = TIMING_INDICATOR_PIXEL_COUNT - count
        for i in range(TIMING_INDICATOR_PIXEL_COUNT):
            self._timing_indicator_bitmap[i, 0] = 1 if i >= first_lit else 0
