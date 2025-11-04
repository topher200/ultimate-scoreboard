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
    ):
        """Initialize a fake label.

        :param font: Font object (typically terminalio.FONT)
        :param str text: Text content, defaults to empty string
        :param int scale: Font scale factor, defaults to 1
        :param int color: Color in 0xRRGGBB format, defaults to white
        :param tuple anchor_point: Anchor point (x, y) as floats between 0.0 and 1.0
        :param tuple anchored_position: Position (x, y) in pixels, defaults to None
        """
        self.font = font
        self._text = text
        self.scale = scale
        self._color = color
        self.anchor_point = anchor_point
        self.anchored_position = anchored_position
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
