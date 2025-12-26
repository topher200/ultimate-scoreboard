"""Tests for TimingIndicatorManager."""

import pytest

from src.display_manager import (
    TIMING_INDICATOR_MAX_DOTS_TO_SHOW,
    TIMING_INDICATOR_REMOVAL_INTERVAL,
)
from src.timing_indicator import TimingIndicatorManager


class TestTimingIndicatorManager:
    """Test TimingIndicatorManager."""

    def test_initialization_defaults(self):
        """Test that TimingIndicatorManager initializes with default constants."""
        manager = TimingIndicatorManager(
            max_dots=TIMING_INDICATOR_MAX_DOTS_TO_SHOW,
            removal_interval=TIMING_INDICATOR_REMOVAL_INTERVAL,
        )
        assert manager.get_dot_count() == 0
        assert manager.removal_interval == TIMING_INDICATOR_REMOVAL_INTERVAL
        assert not manager.has_dots()

    def test_initialization_custom(self):
        """Test that TimingIndicatorManager initializes with custom values."""
        manager = TimingIndicatorManager(max_dots=10, removal_interval=3.0)
        assert manager.get_dot_count() == 0
        assert manager.removal_interval == 3.0
        assert not manager.has_dots()

    def test_refill_dots(self):
        """Test that refill_dots sets count to max."""
        manager = TimingIndicatorManager(max_dots=12, removal_interval=2.0)
        assert manager.get_dot_count() == 0
        manager.refill_dots()
        assert manager.get_dot_count() == 12
        assert manager.has_dots()

    def test_remove_dot_decrements(self):
        """Test that remove_dot decrements count correctly."""
        manager = TimingIndicatorManager(max_dots=5, removal_interval=2.0)
        manager.refill_dots()
        assert manager.get_dot_count() == 5

        manager.remove_dot()
        assert manager.get_dot_count() == 4

        manager.remove_dot()
        assert manager.get_dot_count() == 3

    def test_remove_dot_clamps_to_zero(self):
        """Test that remove_dot clamps to 0."""
        manager = TimingIndicatorManager(max_dots=2, removal_interval=2.0)
        assert manager.get_dot_count() == 0

        manager.remove_dot()
        assert manager.get_dot_count() == 0

        manager.refill_dots()
        manager.remove_dot()
        manager.remove_dot()
        assert manager.get_dot_count() == 0

        manager.remove_dot()
        assert manager.get_dot_count() == 0

    def test_has_dots(self):
        """Test that has_dots returns correct state."""
        manager = TimingIndicatorManager(max_dots=3, removal_interval=2.0)
        assert not manager.has_dots()

        manager.refill_dots()
        assert manager.has_dots()

        manager.remove_dot()
        assert manager.has_dots()

        manager.remove_dot()
        assert manager.has_dots()

        manager.remove_dot()
        assert not manager.has_dots()

    def test_get_dot_count(self):
        """Test that get_dot_count returns current count."""
        manager = TimingIndicatorManager(max_dots=5, removal_interval=2.0)
        assert manager.get_dot_count() == 0

        manager.refill_dots()
        assert manager.get_dot_count() == 5

        for i in range(5):
            assert manager.get_dot_count() == 5 - i
            manager.remove_dot()

        assert manager.get_dot_count() == 0

