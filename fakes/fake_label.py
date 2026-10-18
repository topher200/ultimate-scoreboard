"""Fake Label class for testing without hardware."""


class FakeLabel:
    """Fake implementation of adafruit_display_text.label.Label for testing."""

    def __init__(
        self,
        font,
        text="",
        scale=1,
        color=0xFFFFFF,
        anchor_point=(0.0, 0.0),
        anchored_position=None,
        background_color=None,
        padding_top=0,
        padding_bottom=0,
        padding_left=0,
        padding_right=0,
    ):
        """Initialize a fake label.

        :param font: Font object (typically terminalio.FONT)
        :param str text: Text content, defaults to empty string
        :param int scale: Font scale factor, defaults to 1
        :param int color: Color in 0xRRGGBB format, defaults to white
        :param tuple anchor_point: Anchor point (x, y) as floats between 0.0 and 1.0
        :param tuple anchored_position: Position (x, y) in pixels, defaults to None
        :param int background_color: Background color in 0xRRGGBB format, or None for
            transparent
        :param int padding_top: Pixels added to the background box at the top
        :param int padding_bottom: Pixels added to the background box at the bottom
        :param int padding_left: Pixels added to the background box at the left
        :param int padding_right: Pixels added to the background box at the right
        """
        self.font = font
        self._text = text
        self.scale = scale
        self._color = color
        self.anchor_point = anchor_point
        self.anchored_position = anchored_position
        self.background_color = background_color
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom
        self.padding_left = padding_left
        self.padding_right = padding_right
        self.x = 0
        self.y = 0

    @property
    def text(self):
        """Get the text content."""
        return self._text

    @text.setter
    def text(self, value):
        """Set the text content."""
        self._text = value

    @property
    def color(self):
        """Get the text color."""
        return self._color

    @color.setter
    def color(self, value):
        """Set the text color."""
        self._color = value
