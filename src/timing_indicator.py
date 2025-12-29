"""Manages timing indicator state for score button presses."""


class TimingIndicatorManager:
    """Manages the state of the timing indicator dots.

    Tracks how many dots should be displayed, which decreases over time
    after a score button press.
    """

    def __init__(self, max_dots: int, removal_interval: float):
        """Initialize TimingIndicatorManager.

        :param max_dots: Total number of dots to display when full
        :param removal_interval: Seconds between dot removal
        """
        self._max_dots = max_dots
        self._removal_interval = removal_interval
        self._current_dot_count = 0

    def refill_dots(self) -> None:
        """Reset dot count to maximum."""
        self._current_dot_count = self._max_dots

    def remove_dot(self) -> None:
        """Remove one dot (decrement count, clamped to 0)."""
        if self._current_dot_count > 0:
            self._current_dot_count -= 1

    def get_dot_count(self) -> int:
        """Get current number of dots to display.

        :return: Current dot count (0 to max_dots)
        """
        return self._current_dot_count

    def has_dots(self) -> bool:
        """Check if any dots remain.

        :return: True if dot count > 0, False otherwise
        """
        return self._current_dot_count > 0

    def clear_dots(self) -> None:
        """Clear all dots (set count to 0)."""
        self._current_dot_count = 0

    @property
    def removal_interval(self) -> float:
        """Get the removal interval in seconds."""
        return self._removal_interval
