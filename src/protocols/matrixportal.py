"""Protocol definition for MatrixPortal interface."""

from src.compat import Any, Protocol


class MatrixPortalLike(Protocol):
    """Protocol defining the MatrixPortal interface used in this project."""

    @property
    def display(self) -> Any:
        """Get the display object."""
        ...
