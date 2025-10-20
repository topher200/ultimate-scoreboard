import terminalio
import displayio
from adafruit_display_text import label


# Color constants
RED_COLOR = 0xAA0000
BLUE_COLOR = 0x0000AA

# Display dimensions
DISPLAY_WIDTH = 64
BORDER_MARGIN_WIDTH = 2
HALF_DISPLAY_WIDTH = DISPLAY_WIDTH / 2

# Font and scaling constants
TEAM_NAME_FONT_SCALE = 1
SCORE_FONT_SCALE = 2
FONT_TYPE = terminalio.FONT

# Position constants
SCORE_HEIGHT_RATIO = 0.75
TEAM_NAME_HEIGHT_RATIO = 0.25
SCORE_VERTICAL_OFFSET = -3
TEAM_NAME_VERTICAL_OFFSET = -4
RED_TEAM_NAME_X_POSITION = 4
BLUE_TEAM_NAME_X_POSITION = 36


class ScoreboardTextManager:
    def __init__(self, matrixportal):
        self.matrixportal = matrixportal
        self.display = matrixportal.display
        self.text_elements = {}
        self.main_group = displayio.Group()
        self._setup_layout()
        self.display.show(self.main_group)

    def _setup_layout(self):
        """Initialize all text elements with their positions and properties."""
        display_height = self.display.height

        # Red Score
        red_score_label = label.Label(
            FONT_TYPE,
            text="0",
            scale=SCORE_FONT_SCALE,
            color=RED_COLOR,
        )
        red_score_label.x = BORDER_MARGIN_WIDTH
        red_score_label.y = (
            int(display_height * SCORE_HEIGHT_RATIO) + SCORE_VERTICAL_OFFSET
        )

        self.text_elements["red_score"] = {
            "label": red_score_label,
            "base_scale": SCORE_FONT_SCALE,
            "color": RED_COLOR,
            "base_x": BORDER_MARGIN_WIDTH,
            "base_y": int(display_height * SCORE_HEIGHT_RATIO) + SCORE_VERTICAL_OFFSET,
        }
        self.main_group.append(red_score_label)

        # Blue Score
        blue_score_label = label.Label(
            FONT_TYPE,
            text="0",
            scale=SCORE_FONT_SCALE,
            color=BLUE_COLOR,
        )
        blue_score_label.x = HALF_DISPLAY_WIDTH + BORDER_MARGIN_WIDTH
        blue_score_label.y = (
            int(display_height * SCORE_HEIGHT_RATIO) + SCORE_VERTICAL_OFFSET
        )

        self.text_elements["blue_score"] = {
            "label": blue_score_label,
            "base_scale": SCORE_FONT_SCALE,
            "color": BLUE_COLOR,
            "base_x": HALF_DISPLAY_WIDTH + BORDER_MARGIN_WIDTH,
            "base_y": int(display_height * SCORE_HEIGHT_RATIO) + SCORE_VERTICAL_OFFSET,
        }
        self.main_group.append(blue_score_label)

        # Red Team name
        red_team_label = label.Label(
            FONT_TYPE,
            text="Red",
            scale=TEAM_NAME_FONT_SCALE,
            color=RED_COLOR,
        )
        red_team_label.x = RED_TEAM_NAME_X_POSITION
        red_team_label.y = (
            int(display_height * TEAM_NAME_HEIGHT_RATIO) + TEAM_NAME_VERTICAL_OFFSET
        )

        self.text_elements["red_team"] = {
            "label": red_team_label,
            "base_scale": TEAM_NAME_FONT_SCALE,
            "color": RED_COLOR,
            "base_x": RED_TEAM_NAME_X_POSITION,
            "base_y": int(display_height * TEAM_NAME_HEIGHT_RATIO)
            + TEAM_NAME_VERTICAL_OFFSET,
        }
        self.main_group.append(red_team_label)

        # Blue Team name
        blue_team_label = label.Label(
            FONT_TYPE,
            text="Blue",
            scale=TEAM_NAME_FONT_SCALE,
            color=BLUE_COLOR,
        )
        blue_team_label.x = BLUE_TEAM_NAME_X_POSITION
        blue_team_label.y = (
            int(display_height * TEAM_NAME_HEIGHT_RATIO) + TEAM_NAME_VERTICAL_OFFSET
        )

        self.text_elements["blue_team"] = {
            "label": blue_team_label,
            "base_scale": TEAM_NAME_FONT_SCALE,
            "color": BLUE_COLOR,
            "base_x": BLUE_TEAM_NAME_X_POSITION,
            "base_y": int(display_height * TEAM_NAME_HEIGHT_RATIO)
            + TEAM_NAME_VERTICAL_OFFSET,
        }
        self.main_group.append(blue_team_label)

        # Connecting indicator
        connecting_label = label.Label(
            FONT_TYPE,
            text=" ",
            scale=1,
        )
        connecting_label.x = 59
        connecting_label.y = 0

        self.text_elements["connecting"] = {
            "label": connecting_label,
            "base_scale": 1,
            "color": None,
            "base_x": 59,
            "base_y": 0,
        }
        self.main_group.append(connecting_label)

    def _calculate_dynamic_scale(self, base_scale, text):
        """Calculate scale based on text length. Divide by 2 for every 10+ characters."""
        scale = base_scale
        text_length = len(str(text))

        # Apply scaling: divide by 2 for every 10 characters over the limit
        while text_length > 10:
            scale /= 2
            text_length -= 10

        # Ensure scale doesn't go below 0.5 for readability
        return max(scale, 0.5)

    def set_text(self, element_id, content):
        """Set text content for a specific element with dynamic scaling."""
        if element_id not in self.text_elements:
            raise ValueError(f"Unknown text element: {element_id}")

        element = self.text_elements[element_id]
        label_obj = element["label"]
        dynamic_scale = self._calculate_dynamic_scale(element["base_scale"], content)

        # Update the text content
        label_obj.text = str(content)

        # Update the scale
        label_obj.scale = dynamic_scale

        # Recenter the text if it's a team name (since width changes with scale)
        if element_id in ["red_team", "blue_team"]:
            # For team names, we want to keep them left-aligned at their base position
            # but adjust if they get too wide
            label_obj.x = element["base_x"]
            # If the text is too wide for the display, adjust position
            text_width = label_obj.bounding_box[2] * dynamic_scale
            if text_width > (DISPLAY_WIDTH - element["base_x"]):
                # Adjust x position to fit
                label_obj.x = DISPLAY_WIDTH - text_width - 2

    def get_current_scale(self, element_id):
        """Get the current scale of a text element for debugging."""
        if element_id not in self.text_elements:
            raise ValueError(f"Unknown text element: {element_id}")

        return self.text_elements[element_id]["label"].scale

    def show_connecting(self, show):
        """Show or hide the connecting indicator."""
        if show:
            self.set_text("connecting", ".")
        else:
            self.set_text("connecting", " ")
