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

class TileGrid(_Layer):
    """TileGrid display element."""
    x: int
    y: int

class _VectorShape(_Layer):
    """Vector shape display element."""
    x: int
    y: int
