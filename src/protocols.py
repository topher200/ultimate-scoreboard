"""Protocol definitions for type checking interfaces.

This allows both the real CircuitPython modules and mock CircuitPython modules
to be used interchangeably in type-checked code.
"""

from src.compat import Any, Protocol


class MatrixPortalLike(Protocol):
    """Protocol defining the MatrixPortal interface used in this project."""

    @property
    def display(self) -> Any:
        """Get the display object."""
        ...

    def get_io_feed(self, feed_key: str, detailed: bool = False) -> Any:
        """Get an IO feed value.

        :param feed_key: The feed key to retrieve
        :param detailed: If True, returns detailed structure
        :return: Feed data structure
        """
        ...

    def push_to_io(
        self,
        feed_key: str,
        data: Any,
        metadata: Any | None = None,
        precision: Any | None = None,
    ) -> None:
        """Push a value to an IO feed.

        :param feed_key: The feed key to push to
        :param data: The value to push
        :param metadata: Optional metadata for the feed
        :param precision: Optional precision for numeric values
        """
        ...


class ButtonLike(Protocol):
    """Protocol defining the button interface used in this project."""

    @property
    def value(self) -> bool:
        """Get the button state.

        :return: True if button is released, False if pressed (active-low)
        """
        ...


class BoardLike(Protocol):
    """Protocol defining the board module interface used in this project."""

    BUTTON_UP: Any
    """Pin definition for the up button."""

    BUTTON_DOWN: Any
    """Pin definition for the down button."""

    NEOPIXEL: Any
    """Pin definition for the NeoPixel status LED."""
