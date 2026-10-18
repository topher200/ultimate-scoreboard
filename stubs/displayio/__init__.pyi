"""Type stubs for displayio package."""

from typing import Any, Protocol

class _Layer(Protocol):
    """Protocol for displayable layers that can be added to groups."""

    x: int
    y: int

class Group:
    """Display group that can contain layers."""
    def __init__(self, **kwargs: Any) -> None: ...
    def append(self, layer: _Layer) -> None: ...
    def __getitem__(self, index: int) -> _Layer: ...
    def __len__(self) -> int: ...

class Bitmap:
    """2D array of palette indices."""
    def __init__(self, width: int, height: int, value_count: int) -> None: ...
    def __getitem__(self, index: tuple[int, int]) -> int: ...
    def __setitem__(self, index: tuple[int, int], value: int) -> None: ...

class Palette:
    """Map from palette index to color."""
    def __init__(self, color_count: int) -> None: ...
    def __setitem__(self, index: int, color: int) -> None: ...
    def make_transparent(self, palette_index: int) -> None: ...

class TileGrid(_Layer):
    """TileGrid display element."""

    x: int
    y: int
    hidden: bool
    bitmap: Bitmap
    def __init__(
        self, bitmap: Bitmap, *, pixel_shader: Palette, x: int = 0, y: int = 0
    ) -> None: ...

class _VectorShape(_Layer):
    """Vector shape display element."""

    x: int
    y: int
