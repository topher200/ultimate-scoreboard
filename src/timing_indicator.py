"""Manages timing indicator state for score button presses."""

import time

from src.compat import Callable

# Time from a goal to the pull, per USA Ultimate rules
TIMING_INDICATOR_DURATION_SECONDS = 80
TIMING_INDICATOR_PIXEL_COUNT = 60
TIMING_INDICATOR_REMOVAL_INTERVAL = (
    TIMING_INDICATOR_DURATION_SECONDS / TIMING_INDICATOR_PIXEL_COUNT
)


class TimingIndicatorManager:
    """Manages the state of the timing indicator dots.

    Tracks how many dots should be displayed, which decreases over time
    after a score button press.
    """

    def __init__(
        self,
        max_dots: int,
        removal_interval: float,
        get_time: Callable = time.monotonic,
    ):
        """Initialize TimingIndicatorManager.

        :param max_dots: Total number of dots to display when full
        :param removal_interval: Seconds between dot removal
        :param get_time: Callable returning current time in seconds
        """
        self._max_dots = max_dots
        self._removal_interval = removal_interval
        self._get_time = get_time
        self._current_dot_count = 0
        self._next_removal_at = 0.0

    def refill_dots(self) -> None:
        """Reset dot count to maximum and restart the removal schedule."""
        self._current_dot_count = self._max_dots
        self._next_removal_at = self._get_time() + self._removal_interval

    def remove_due_dots(self) -> bool:
        """Remove one dot for each removal interval that has passed.

        :return: True if the dot count changed
        """
        now = self._get_time()
        changed = False
        while self._current_dot_count > 0 and now >= self._next_removal_at:
            self._current_dot_count -= 1
            self._next_removal_at += self._removal_interval
            changed = True
        return changed

    def get_dot_count(self) -> int:
        """Get current number of dots to display.

        :return: Current dot count (0 to max_dots)
        """
        return self._current_dot_count

    def clear_dots(self) -> None:
        """Clear all dots (set count to 0)."""
        self._current_dot_count = 0
