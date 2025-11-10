"""Protocol definition for button interface."""

from src.compat import Protocol


class ButtonLike(Protocol):
    """Protocol defining the button interface used in this project."""

    @property
    def value(self) -> bool:
        """Get the button state.

        :return: True if button is released, False if pressed (active-low)
        """
        ...

