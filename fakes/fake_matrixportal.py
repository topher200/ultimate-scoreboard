"""Fake MatrixPortal and Display classes for testing without hardware."""


class FakeDisplay:
    """Fake implementation of displayio.Display for testing."""

    def __init__(self):
        """Initialize a fake display."""
        self._root_group = None

    @property
    def root_group(self):
        """Get the root display group."""
        return self._root_group

    @root_group.setter
    def root_group(self, value):
        """Set the root display group."""
        self._root_group = value


class FakeMatrixPortal:
    """Fake implementation of MatrixPortal for testing without hardware."""

    def __init__(self, **kwargs):
        """Initialize a fake matrix portal.

        Accepts any keyword arguments for compatibility with real MatrixPortal,
        but doesn't use them since this is a fake.
        """
        self._display = FakeDisplay()

    @property
    def display(self):
        """Get the display object."""
        return self._display
