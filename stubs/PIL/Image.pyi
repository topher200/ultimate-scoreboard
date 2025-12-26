"""Type stubs for PIL.Image module."""

class Image:
    """PIL Image class."""

    def convert(self, mode: str) -> Image: ...
    def tobytes(self) -> bytes: ...
    @property
    def size(self) -> tuple[int, int]: ...

# Module-level function
def new(
    mode: str, size: tuple[int, int], color: tuple[int, int, int] | None = None
) -> Image: ...
