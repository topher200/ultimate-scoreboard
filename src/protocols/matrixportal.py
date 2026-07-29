"""Protocol definition for MatrixPortal interface."""

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

