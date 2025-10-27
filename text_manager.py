import terminalio
import displayio
from adafruit_display_text import label


# Color constants
LEFT_TEAM_COLOR = 0xAA0000  # red
RIGHT_TEAM_COLOR = 0x0000AA  # blue

# Display dimensions
DISPLAY_WIDTH = 64
BORDER_MARGIN_WIDTH = 2
HALF_DISPLAY_WIDTH = DISPLAY_WIDTH // 2

# Font and scaling constants
TEAM_NAME_FONT_SCALE = 1
SCORE_FONT_SCALE = 2
FONT_TYPE = terminalio.FONT

# Position constants
LEFT_TEAM_NAME_X_POSITION = 4
RIGHT_TEAM_NAME_X_POSITION = 36
SCORE_START_Y_RATIO_OFFSET = 0.25  # start of score at 25% of display height


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
        display_height = self.display.height

        # Left Team name
        team_name_y = 0
        left_team_label = label.Label(
            FONT_TYPE,
            text="",
            scale=TEAM_NAME_FONT_SCALE,
            color=LEFT_TEAM_COLOR,
            anchor_point=(0.0, 0.0),  # Top-left
            anchored_position=(
                LEFT_TEAM_NAME_X_POSITION,
                team_name_y,
            ),
        )
        self.text_elements["left_team"] = {
            "label": left_team_label,
            "color": LEFT_TEAM_COLOR,
            "base_y": team_name_y,
        }
        self.main_group.append(left_team_label)

        # Right Team name (right-justified)
        team_name_y = 0
        right_team_label = label.Label(
            FONT_TYPE,
            text="",
            scale=TEAM_NAME_FONT_SCALE,
            color=RIGHT_TEAM_COLOR,
            anchor_point=(1.0, 0.0),  # Top-right
            anchored_position=(RIGHT_TEAM_NAME_X_POSITION, team_name_y),
        )
        self.text_elements["right_team"] = {
            "label": right_team_label,
            "color": RIGHT_TEAM_COLOR,
            "base_y": team_name_y,
            "right_anchor": True,
        }
        self.main_group.append(right_team_label)

        # Left Team Score
        score_y = int(display_height * SCORE_START_Y_RATIO_OFFSET)
        left_team_score_label = label.Label(
            FONT_TYPE,
            text="0",
            scale=SCORE_FONT_SCALE,
            color=LEFT_TEAM_COLOR,
            anchor_point=(0.0, 0.0),  # Top-left
            anchored_position=(BORDER_MARGIN_WIDTH, score_y),
        )
        self.text_elements["left_team_score"] = {
            "label": left_team_score_label,
            "color": LEFT_TEAM_COLOR,
            "base_y": score_y,
        }
        self.main_group.append(left_team_score_label)

        # Right Team Score (right-justified)
        score_y = int(display_height * SCORE_START_Y_RATIO_OFFSET)
        right_team_score_label = label.Label(
            FONT_TYPE,
            text="0",
            scale=SCORE_FONT_SCALE,
            color=RIGHT_TEAM_COLOR,
            anchor_point=(1.0, 0.0),  # Top-right
            anchored_position=(DISPLAY_WIDTH - BORDER_MARGIN_WIDTH, score_y),
        )
        self.text_elements["right_team_score"] = {
            "label": right_team_score_label,
            "color": RIGHT_TEAM_COLOR,
            "base_y": score_y,
            "right_anchor": True,  # Flag to indicate right-justified
        }
        self.main_group.append(right_team_score_label)

        # Connecting indicator
        connecting_label = label.Label(FONT_TYPE, text=" ")
        connecting_label.x = 59
        connecting_label.y = 0
        self.text_elements["connecting"] = {
            "label": connecting_label,
            "color": None,
            "base_x": 59,
            "base_y": 0,
        }
        self.main_group.append(connecting_label)

    def set_text(self, element_id, content):
        """Set text content for a specific element."""
        if element_id not in self.text_elements:
            raise ValueError(f"Unknown text element: {element_id}")

        element = self.text_elements[element_id]
        label_obj = element["label"]

        # Update the text content
        label_obj.text = str(content)

        # Update anchored_position for right-anchored elements
        if element.get("right_anchor"):
            # Update the anchored_position x coordinate while keeping y
            base_y = element.get("base_y", 0)
            label_obj.anchored_position = (
                DISPLAY_WIDTH - BORDER_MARGIN_WIDTH,
                base_y,
            )

    def show_connecting(self, show):
        """Show or hide the connecting indicator."""
        if show:
            self.set_text("connecting", ".")
        else:
            self.set_text("connecting", " ")
