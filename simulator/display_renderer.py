"""Renderer that converts a displayio.Group hierarchy to an LED matrix image."""

from displayio._area import Area
from displayio._structs import ColorspaceStruct
from PIL import Image, ImageChops, ImageDraw

from src.display_manager import DISPLAY_HEIGHT, DISPLAY_WIDTH

# Bits per color channel that the MatrixPortal drives each LED with
MATRIX_BIT_DEPTH = 2
UNLIT_LED_COLOR = (24, 24, 24)
LED_DIAMETER_FRACTION = 0.8


def render_pixels(root_group) -> list[int]:
    """Render a Blinka displayio group to 0xRRGGBB pixels.

    Blinka draws the group with a port of CircuitPython's fill code, so labels
    pick up the real terminalio font, anchors, and scaling.

    :param root_group: The root displayio.Group to render
    :return: DISPLAY_WIDTH * DISPLAY_HEIGHT colors in row order (0 is unlit)
    """
    pixel_count = DISPLAY_WIDTH * DISPLAY_HEIGHT
    buffer = memoryview(bytearray(pixel_count * 4)).cast("I")
    mask = memoryview(bytearray((pixel_count + 31) // 32 * 4)).cast("I")
    if root_group is not None:
        root_group._fill_area(
            ColorspaceStruct(depth=32),
            Area(0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT),
            mask,
            buffer,
        )
    return list(buffer)


_LEVELS = (1 << MATRIX_BIT_DEPTH) - 1
# sRGB value for the light output of each brightness level the matrix can show
_LEVEL_TO_SRGB = [
    round(255 * (level / _LEVELS) ** (1 / 2.2)) for level in range(_LEVELS + 1)
]


def _led_color(color: int) -> tuple[int, int, int]:
    if color == 0:
        return UNLIT_LED_COLOR
    red, green, blue = (
        _LEVEL_TO_SRGB[((color >> shift) & 0xFF) >> (8 - MATRIX_BIT_DEPTH)]
        for shift in (16, 8, 0)
    )
    return (red, green, blue)


class DisplayRenderer:
    """Renders a displayio.Group hierarchy as a grid of LEDs."""

    def __init__(self):
        """Initialize the display renderer."""
        self._led_masks: dict[int, Image.Image] = {}

    def _led_mask(self, target_scale: int) -> Image.Image:
        """Get a full-size mask that is white inside each LED and black between."""
        if target_scale not in self._led_masks:
            cell = Image.new("RGB", (target_scale, target_scale))
            inset = target_scale * (1 - LED_DIAMETER_FRACTION) / 2
            ImageDraw.Draw(cell).ellipse(
                (inset, inset, target_scale - inset, target_scale - inset),
                fill=(255, 255, 255),
            )
            mask = Image.new(
                "RGB", (DISPLAY_WIDTH * target_scale, DISPLAY_HEIGHT * target_scale)
            )
            for y in range(DISPLAY_HEIGHT):
                for x in range(DISPLAY_WIDTH):
                    mask.paste(cell, (x * target_scale, y * target_scale))
            self._led_masks[target_scale] = mask
        return self._led_masks[target_scale]

    def render(self, root_group, target_scale: int) -> Image.Image:
        """Render the display root group to an image of the LED matrix.

        :param root_group: The root displayio.Group to render
        :param target_scale: Size of each LED in image pixels
        :return: PIL Image of size (DISPLAY_WIDTH * target_scale, DISPLAY_HEIGHT * target_scale)
        """
        image = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        image.putdata([_led_color(color) for color in render_pixels(root_group)])
        image = image.resize(
            (DISPLAY_WIDTH * target_scale, DISPLAY_HEIGHT * target_scale),
            Image.Resampling.NEAREST,
        )
        return ImageChops.multiply(image, self._led_mask(target_scale))
