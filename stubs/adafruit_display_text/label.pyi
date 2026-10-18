"""Type stubs for adafruit_display_text.label module."""

from typing import Any

from displayio import _Layer

class Label(_Layer):
    """Label class for displaying text on displays."""

    x: int
    y: int
    text: str
    color: int | None
    background_color: int | None
    scale: int

    def __init__(
        self,
        font: Any,
        *,
        text: str = "",
        color: int | None = None,
        scale: int = 1,
        background_color: int | None = None,
        padding_top: int = 0,
        padding_bottom: int = 0,
        padding_left: int = 0,
        padding_right: int = 0,
        **kwargs: Any,
    ) -> None: ...
