"""Type stubs for adafruit_display_text.label module."""

from typing import Any

from displayio import Group, _Layer

class Label(_Layer):
    """Label class for displaying text on displays."""

    x: int
    y: int
    text: str
    color: int | None
    scale: int
    hidden: bool
    anchored_position: tuple[int, int]
    _local_group: Group

    def __init__(
        self,
        font: Any,
        *,
        text: str = "",
        color: int | None = None,
        scale: int = 1,
        **kwargs: Any,
    ) -> None: ...
