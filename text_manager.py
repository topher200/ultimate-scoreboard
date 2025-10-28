import terminalio
import displayio
from adafruit_display_text import label


# Color constants
LEFT_TEAM_COLOR = 0xAA0000  # red
RIGHT_TEAM_COLOR = 0x0000AA  # blue

# Font and scaling constants
TEAM_NAME_FONT_SCALE = 1
SCORE_FONT_SCALE = 2
FONT_TYPE = terminalio.FONT

# Display dimensions
DISPLAY_HEIGHT = 32
DISPLAY_WIDTH = 64
LEFT_BORDER_MARGIN_WIDTH = 2

# Position constants
TEAM_NAME_Y_POSITION = 0
SCORE_Y_POSITION = int(DISPLAY_HEIGHT * 0.25)
LEFT_JUSTIFY_ANCHOR_POINT = (0.0, 0.0)
RIGHT_JUSTIFY_ANCHOR_POINT = (1.0, 0.0)


class ScoreboardTextManager:
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.display = matrixportal.display
        self.text_elements = {}
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

        # 'Connecting' indicator
        connecting_label = label.Label(FONT_TYPE, text=" ")
        connecting_label.x = DISPLAY_WIDTH - 5  # number may not be accurate
        connecting_label.y = DISPLAY_HEIGHT - 5  # number may not be accurate
        self.text_elements["connecting"] = {"label": connecting_label}
        self.text_elements["connecting"] = {"label": connecting_label}
        self.main_group.append(connecting_label)

    def set_text(self, element_id, content):
        """Set text content for a specific element."""
        if element_id not in self.text_elements:
            raise ValueError(f"Unknown text element: {element_id}")
        element = self.text_elements[element_id]
        label_obj = element["label"]
        label_obj.text = str(content)

    def show_connecting(self, show):
        """Show or hide the connecting indicator."""
        if show:
            self.set_text("connecting", ".")
        else:
            self.set_text("connecting", " ")
