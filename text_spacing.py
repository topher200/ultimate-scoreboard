import time
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal

RED_COLOR = 0xAA0000
BLUE_COLOR = 0x0000AA

BORDER_MARGIN_WIDTH = 2
TOTAL_PIXELS_WITDTH = 64
HALF_TOTAL_PIXELS_WITDTH = TOTAL_PIXELS_WITDTH / 2


def set(matrixportal):
    # Red Score
    matrixportal.add_text(
        text_font=terminalio.FONT,
        text_position=(
            BORDER_MARGIN_WIDTH,
            int(matrixportal.graphics.display.height * 0.75) - 3,
        ),
        text_color=RED_COLOR,
        text_scale=2,
    )

    # Blue Score
    matrixportal.add_text(
        text_font=terminalio.FONT,
        text_position=(
            HALF_TOTAL_PIXELS_WITDTH + BORDER_MARGIN_WIDTH,
            int(matrixportal.graphics.display.height * 0.75) - 3,
        ),
        text_color=BLUE_COLOR,
        text_scale=2,
    )

    # Red Team name
    matrixportal.add_text(
        text_font=terminalio.FONT,
        text_position=(4, int(matrixportal.graphics.display.height * 0.25) - 4),
        text_color=RED_COLOR,
    )

    # Blue Team name
    matrixportal.add_text(
        text_font=terminalio.FONT,
        text_position=(36, int(matrixportal.graphics.display.height * 0.25) - 4),
        text_color=BLUE_COLOR,
    )
