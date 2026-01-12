import displayio
import terminalio
from adafruit_display_text import label

# Color constants
LEFT_TEAM_COLOR = 0xAA0000  # AWAY team color (red)
RIGHT_TEAM_COLOR = 0x00AA00  # HOME team color (green)
MMP_GENDER_MATCHUP_COLOR = 0xFFA500  # orange
WMP_GENDER_MATCHUP_COLOR = 0xFFA500  # orange

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
TIMING_INDICATOR_MAX_DOTS_WHEN_FULL = 12
TIMING_INDICATOR_MAX_DOTS_TO_SHOW = 4
TIMING_INDICATOR_Y_POSITION = DISPLAY_HEIGHT - 5
TIMING_INDICATOR_DOT_CHAR = "."
TIMING_INDICATOR_REMOVAL_INTERVAL = 2.0


class DisplayManager:
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.display = matrixportal.display
        self.text_elements = {}
        self.timing_indicator_dots = []
        self.main_group = displayio.Group()
        self._setup_layout()
        self.display.root_group = self.main_group

    def _setup_layout(self):
        """Initialize all text elements with their positions and properties."""
        # Left Team name
        left_team_label = label.Label(
            FONT_TYPE,
            text="",
            scale=TEAM_NAME_FONT_SCALE,
            color=LEFT_TEAM_COLOR,
            anchor_point=LEFT_JUSTIFY_ANCHOR_POINT,
            anchored_position=(LEFT_BORDER_MARGIN_WIDTH, TEAM_NAME_Y_POSITION),
        )
        self.text_elements["left_team"] = {"label": left_team_label}
        self.main_group.append(left_team_label)

        # Right Team name (right-justified)
        right_team_label = label.Label(
            FONT_TYPE,
            text="",
            scale=TEAM_NAME_FONT_SCALE,
            color=RIGHT_TEAM_COLOR,
            anchor_point=RIGHT_JUSTIFY_ANCHOR_POINT,
            anchored_position=(DISPLAY_WIDTH, TEAM_NAME_Y_POSITION),
        )
        self.text_elements["right_team"] = {"label": right_team_label}
        self.main_group.append(right_team_label)

        # Left Team Score
        left_team_score_label = label.Label(
            FONT_TYPE,
            text="",
            scale=SCORE_FONT_SCALE,
            color=LEFT_TEAM_COLOR,
            anchor_point=LEFT_JUSTIFY_ANCHOR_POINT,
            anchored_position=(LEFT_BORDER_MARGIN_WIDTH, SCORE_Y_POSITION),
        )
        self.text_elements["left_team_score"] = {"label": left_team_score_label}
        self.main_group.append(left_team_score_label)

        # Right Team Score (right-justified)
        right_team_score_label = label.Label(
            FONT_TYPE,
            text="",
            scale=SCORE_FONT_SCALE,
            color=RIGHT_TEAM_COLOR,
            anchor_point=RIGHT_JUSTIFY_ANCHOR_POINT,
            anchored_position=(DISPLAY_WIDTH, SCORE_Y_POSITION),
        )
        self.text_elements["right_team_score"] = {"label": right_team_score_label}
        self.main_group.append(right_team_score_label)

        # Gender matchup
        gender_matchup_label = label.Label(
            FONT_TYPE,
            text=" ",
            scale=GENDER_MATCHUP_FONT_SCALE,
            color=WMP_GENDER_MATCHUP_COLOR,
            anchor_point=MIDDLE_JUSTIFY_ANCHOR_POINT,
            anchored_position=(GENDER_MATCHUP_X_POSITION, GENDER_MATCHUP_Y_POSITION),
        )
        self.text_elements["gender_matchup"] = {"label": gender_matchup_label}
        self.main_group.append(gender_matchup_label)

        # Gender matchup counter
        gender_matchup_counter_label = label.Label(
            FONT_TYPE,
            text=" ",
            scale=GENDER_MATCHUP_FONT_SCALE,
            color=WMP_GENDER_MATCHUP_COLOR,
            anchor_point=MIDDLE_JUSTIFY_ANCHOR_POINT,
            anchored_position=(
                GENDER_MATCHUP_X_POSITION,
                GENDER_MATCHUP_Y_POSITION + 10,
            ),
        )
        self.text_elements["gender_matchup_counter"] = {
            "label": gender_matchup_counter_label
        }
        self.main_group.append(gender_matchup_counter_label)

        # 'Connecting' indicator
        connecting_label = label.Label(FONT_TYPE, text=" ", color=0xFFFF00)
        connecting_label.x = DISPLAY_WIDTH - 5  # number may not be accurate
        connecting_label.y = DISPLAY_HEIGHT - 5  # number may not be accurate
        self.text_elements["connecting"] = {"label": connecting_label}
        self.main_group.append(connecting_label)

        # Timing indicator dots
        self._setup_timing_indicator()

    def _get_gender_matchup_color(self, gender_matchup):
        if "MMP" in gender_matchup:
            return MMP_GENDER_MATCHUP_COLOR
        else:
            return WMP_GENDER_MATCHUP_COLOR

    def set_text(self, element_id, content):
        """Set text content for a specific element."""
        if element_id not in self.text_elements:
            raise ValueError(f"Unknown text element: {element_id}")
        element = self.text_elements[element_id]
        label_obj = element["label"]
        label_obj.text = str(content)
        if element_id in {"gender_matchup", "gender_matchup_counter"}:
            label_obj.color = self._get_gender_matchup_color(content)

    def show_connecting(self, show):
        """Show or hide the connecting indicator."""
        if show:
            self.set_text("connecting", ".")
        else:
            self.set_text("connecting", " ")

    def _setup_timing_indicator(self):
        """Initialize timing indicator dots along the bottom of the screen."""
        available_width = DISPLAY_WIDTH - 2 * LEFT_BORDER_MARGIN_WIDTH
        dot_spacing = available_width / TIMING_INDICATOR_MAX_DOTS_WHEN_FULL
        start_x = LEFT_BORDER_MARGIN_WIDTH
        first_dot_index = (
            TIMING_INDICATOR_MAX_DOTS_WHEN_FULL - TIMING_INDICATOR_MAX_DOTS_TO_SHOW
        )

        for i in range(TIMING_INDICATOR_MAX_DOTS_TO_SHOW):
            x_pos = int(start_x + (first_dot_index + i) * dot_spacing)
            dot_label = label.Label(
                FONT_TYPE,
                text=" ",
                scale=1,
                color=0xFFFFFF,  # White color for dots
            )
            dot_label.x = x_pos
            dot_label.y = TIMING_INDICATOR_Y_POSITION
            self.timing_indicator_dots.append(dot_label)
            self.main_group.append(dot_label)

    def update_timing_indicator(self, count: int) -> None:
        """Update timing indicator to show specified number of dots.

        :param count: Number of dots to display (0 to max_dots)
        """
        count = max(0, min(count, TIMING_INDICATOR_MAX_DOTS_TO_SHOW))
        for i, dot_label in enumerate(self.timing_indicator_dots):
            if i >= (TIMING_INDICATOR_MAX_DOTS_TO_SHOW - count):
                dot_label.text = TIMING_INDICATOR_DOT_CHAR
            else:
                dot_label.text = " "
