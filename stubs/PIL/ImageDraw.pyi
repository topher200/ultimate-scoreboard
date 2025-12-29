"""Type stubs for PIL.ImageDraw module."""

from typing import Any

from .Image import Image

class Draw:
    """PIL ImageDraw.Draw class."""

    def __init__(self, image: Image) -> None: ...
    def text(
        self,
        xy: tuple[int, int],
        text: str,
        fill: tuple[int, int, int] | None = None,
        font: Any | None = None,
    ) -> None: ...
    def textbbox(
        self, xy: tuple[int, int], text: str, font: Any | None = None
    ) -> tuple[int, int, int, int]: ...
