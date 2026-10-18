"""Tests for TimingIndicatorManager."""

import pytest

from src.timing_indicator import (
    TIMING_INDICATOR_PIXEL_COUNT,
    TIMING_INDICATOR_REMOVAL_INTERVAL,
    TimingIndicatorManager,
)


class FakeClock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def _manager(max_dots=5, removal_interval=2.0):
    clock = FakeClock()
    manager = TimingIndicatorManager(
        max_dots=max_dots, removal_interval=removal_interval, get_time=clock
    )
    return manager, clock


class TestTimingIndicatorManager:
    """Test TimingIndicatorManager."""

    def test_matches_usau_pull_time(self):
        """Test that the full timing indicator lasts 80 seconds."""
        assert TIMING_INDICATOR_PIXEL_COUNT * TIMING_INDICATOR_REMOVAL_INTERVAL == (
            pytest.approx(80)
        )

    def test_starts_empty(self):
        manager, _ = _manager()
        assert manager.get_dot_count() == 0

    def test_refill_dots(self):
        manager, _ = _manager(max_dots=12)
        manager.refill_dots()
        assert manager.get_dot_count() == 12

    def test_no_removal_before_interval(self):
        manager, clock = _manager()
        manager.refill_dots()
        clock.now += 1.9
        assert not manager.remove_due_dots()
        assert manager.get_dot_count() == 5

    def test_removes_one_dot_per_interval(self):
        manager, clock = _manager()
        manager.refill_dots()
        clock.now += 2.0
        assert manager.remove_due_dots()
        assert manager.get_dot_count() == 4
        assert not manager.remove_due_dots()
        clock.now += 2.0
        assert manager.remove_due_dots()
        assert manager.get_dot_count() == 3

    def test_catches_up_after_a_late_poll(self):
        manager, clock = _manager()
        manager.refill_dots()
        clock.now += 6.5
        assert manager.remove_due_dots()
        assert manager.get_dot_count() == 2

    def test_stops_at_zero(self):
        manager, clock = _manager(max_dots=2)
        manager.refill_dots()
        clock.now += 100
        manager.remove_due_dots()
        assert manager.get_dot_count() == 0
        assert not manager.remove_due_dots()

    def test_refill_restarts_schedule(self):
        manager, clock = _manager()
        manager.refill_dots()
        clock.now += 1.5
        manager.refill_dots()
        clock.now += 1.0
        assert not manager.remove_due_dots()
        assert manager.get_dot_count() == 5
        clock.now += 1.0
        assert manager.remove_due_dots()
        assert manager.get_dot_count() == 4

    def test_clear_dots(self):
        manager, _ = _manager()
        manager.refill_dots()
        manager.clear_dots()
        assert manager.get_dot_count() == 0
