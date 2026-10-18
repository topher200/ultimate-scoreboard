"""Type stubs for PIL.ImageDraw module."""

from .Image import Image

class Draw:
    """PIL ImageDraw.Draw class."""

    def __init__(self, image: Image) -> None: ...
    def ellipse(
        self,
        xy: tuple[float, float, float, float],
        fill: tuple[int, int, int] | None = None,
    ) -> None: ...
