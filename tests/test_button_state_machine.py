"""Tests for ButtonStateMachine."""

from src.button_state_machine import (
    ACTION_CHORD,
    ACTION_HOLD_BOTH,
    ACTION_LONG_HOLD_BOTH,
    ACTION_SINGLE,
    LONG_HOLD_THRESHOLD,
    SIMULTANEOUS_HOLD_THRESHOLD,
    ButtonStateMachine,
)

L = "left"
R = "right"
SINGLE_L = (ACTION_SINGLE, L)
SINGLE_R = (ACTION_SINGLE, R)
CHORD_LR = (ACTION_CHORD, L, R)
CHORD_RL = (ACTION_CHORD, R, L)
HOLD_BOTH = (ACTION_HOLD_BOTH,)
LONG_HOLD_BOTH = (ACTION_LONG_HOLD_BOTH,)


def press(button):
    return (button, True)


def release(button):
    return (button, False)


class Driver:
    """Steps a ButtonStateMachine with a fake clock and records its actions."""

    def __init__(self):
        self.machine = ButtonStateMachine((L, R))
        self.now = 0.0
        self.actions = []

    def step(self, *events, wait=0.02):
        """Advance the clock by wait, then step with events and one idle step."""
        self.now += wait
        for evts in (list(events), []):
            action = self.machine.step(evts, self.now)
            if action is not None:
                self.actions.append(action)
        return self


class TestSinglePress:
    def test_fires_on_release_not_on_press(self):
        d = Driver().step(press(L))
        assert d.actions == []
        d.step(release(L))
        assert d.actions == [SINGLE_L]

    def test_press_and_release_in_one_step(self):
        assert Driver().step(press(R), release(R)).actions == [SINGLE_R]


class TestChord:
    def test_fires_when_tapped_button_releases(self):
        d = Driver().step(press(L)).step(press(R))
        assert d.actions == []
        d.step(release(R)).step(release(L))
        assert d.actions == [CHORD_LR]

    def test_other_order(self):
        d = Driver().step(press(R)).step(press(L)).step(release(L)).step(release(R))
        assert d.actions == [CHORD_RL]

    def test_fires_when_held_button_releases_first(self):
        d = Driver().step(press(R)).step(press(L)).step(release(R)).step(release(L))
        assert d.actions == [CHORD_RL]

    def test_repeats_while_held(self):
        d = Driver().step(press(R))
        for _ in range(3):
            d.step(press(L)).step(release(L))
        d.step(release(R))
        assert d.actions == [CHORD_RL] * 3

    def test_tap_inside_one_step_while_held(self):
        d = Driver().step(press(L)).step(press(R), release(R))
        assert d.actions == [CHORD_LR]

    def test_single_press_works_after_chord(self):
        d = Driver().step(press(L)).step(press(R)).step(release(L), release(R))
        d.step(press(L)).step(release(L))
        assert d.actions == [CHORD_LR, SINGLE_L]


class TestHoldBoth:
    def test_simultaneous_press_held(self):
        d = Driver().step(press(L), press(R))
        d.step(wait=SIMULTANEOUS_HOLD_THRESHOLD)
        assert d.actions == [HOLD_BOTH]
        d.step(release(L), release(R))
        assert d.actions == [HOLD_BOTH]

    def test_staggered_press_held_resets_without_chord(self):
        d = Driver().step(press(L)).step(press(R), wait=0.3)
        d.step(wait=SIMULTANEOUS_HOLD_THRESHOLD)
        d.step(release(L)).step(release(R))
        assert d.actions == [HOLD_BOTH]

    def test_not_before_threshold(self):
        d = Driver().step(press(L), press(R))
        d.step(wait=SIMULTANEOUS_HOLD_THRESHOLD - 0.1)
        assert d.actions == []

    def test_simultaneous_quick_release_does_nothing(self):
        d = Driver().step(press(L), press(R)).step(release(L), release(R))
        assert d.actions == []
        assert d.machine.is_idle

    def test_tap_after_reset_while_holding_does_nothing(self):
        d = Driver().step(press(L), press(R)).step(wait=SIMULTANEOUS_HOLD_THRESHOLD)
        d.step(release(R)).step(press(R)).step(release(R)).step(release(L))
        assert d.actions == [HOLD_BOTH]

    def test_single_press_works_after_reset(self):
        d = Driver().step(press(R)).step(press(L))
        d.step(wait=SIMULTANEOUS_HOLD_THRESHOLD)
        d.step(release(R), release(L)).step(press(L)).step(release(L))
        assert d.actions == [HOLD_BOTH, SINGLE_L]

    def test_button_works_after_aborted_simultaneous_press(self):
        """A release seen while waiting must not make the next press fire early."""
        d = Driver().step(press(L), press(R)).step(release(L)).step(release(R))
        d.step(press(R))
        assert d.actions == []
        d.step(release(R))
        assert d.actions == [SINGLE_R]


class TestLongHoldBoth:
    def test_fires_after_hold_both(self):
        d = Driver().step(press(L), press(R))
        d.step(wait=SIMULTANEOUS_HOLD_THRESHOLD)
        d.step(wait=LONG_HOLD_THRESHOLD - SIMULTANEOUS_HOLD_THRESHOLD)
        assert d.actions == [HOLD_BOTH, LONG_HOLD_BOTH]
        d.step(release(L), release(R))
        assert d.actions == [HOLD_BOTH, LONG_HOLD_BOTH]
        assert d.machine.is_idle

    def test_not_before_threshold(self):
        d = Driver().step(press(L), press(R))
        d.step(wait=LONG_HOLD_THRESHOLD - 0.1)
        assert d.actions == [HOLD_BOTH]

    def test_release_before_threshold_cancels(self):
        d = Driver().step(press(L), press(R))
        d.step(wait=SIMULTANEOUS_HOLD_THRESHOLD)
        d.step(release(L)).step(press(L)).step(wait=LONG_HOLD_THRESHOLD)
        d.step(release(L), release(R))
        assert d.actions == [HOLD_BOTH]
