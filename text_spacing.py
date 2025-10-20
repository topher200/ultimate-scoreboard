import terminalio


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


def set(matrixportal):
    display_height = matrixportal.graphics.display.height

    # Red Score
    matrixportal.add_text(
        text_font=FONT_TYPE,
        text_position=(
            BORDER_MARGIN_WIDTH,
            int(display_height * SCORE_HEIGHT_RATIO) + SCORE_VERTICAL_OFFSET,
        ),
        text_color=RED_COLOR,
        text_scale=SCORE_FONT_SCALE,
    )

    # Blue Score
    matrixportal.add_text(
        text_font=FONT_TYPE,
        text_position=(
            HALF_DISPLAY_WIDTH + BORDER_MARGIN_WIDTH,
            int(display_height * SCORE_HEIGHT_RATIO) + SCORE_VERTICAL_OFFSET,
        ),
        text_color=BLUE_COLOR,
        text_scale=SCORE_FONT_SCALE,
    )

    # Red Team name
    matrixportal.add_text(
        text_font=FONT_TYPE,
        text_position=(
            RED_TEAM_NAME_X_POSITION,
            int(display_height * TEAM_NAME_HEIGHT_RATIO) + TEAM_NAME_VERTICAL_OFFSET,
        ),
        text_color=RED_COLOR,
        text_scale=TEAM_NAME_FONT_SCALE,
    )

    # Blue Team name
    matrixportal.add_text(
        text_font=FONT_TYPE,
        text_position=(
            BLUE_TEAM_NAME_X_POSITION,
            int(display_height * TEAM_NAME_HEIGHT_RATIO) + TEAM_NAME_VERTICAL_OFFSET,
        ),
        text_color=BLUE_COLOR,
        text_scale=TEAM_NAME_FONT_SCALE,
    )
