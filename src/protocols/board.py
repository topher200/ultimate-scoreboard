"""Protocol definition for board module interface."""

from src.compat import Any, Protocol


class BoardLike(Protocol):
    """Protocol defining the board module interface used in this project."""

    BUTTON_UP: Any
    """Pin definition for the up button."""

    BUTTON_DOWN: Any
    """Pin definition for the down button."""

    A1: Any
    """Pin definition for analog pin A1 (left button)."""

    A3: Any
    """Pin definition for analog pin A3 (right button)."""

    NEOPIXEL: Any
    """Pin definition for the NeoPixel status LED."""
