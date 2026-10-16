"""Turns two-button press and release events into scoreboard gestures."""

# Hold threshold for long simultaneous press (seconds)
SIMULTANEOUS_HOLD_THRESHOLD = 1.0

ACTION_SINGLE = "single"
ACTION_CHORD = "chord"
ACTION_HOLD_BOTH = "hold_both"

_STATE_IDLE = "idle"
_STATE_SINGLE_HELD = "single_held"
_STATE_BOTH_DOWN = "both_down"
_STATE_WAIT_RELEASE = "wait_release"


class ButtonStateMachine:
    """Recognizes single presses, chords, and holding both buttons.

    Every action fires on a release, except holding both:

    - Single press: (ACTION_SINGLE, button) on release if no chord happened
    - Chord (hold A, tap B): (ACTION_CHORD, A, B) when either button is
      released, if both were down for less than SIMULTANEOUS_HOLD_THRESHOLD.
      While A stays down, each further tap of B repeats the chord.
    - Both down for SIMULTANEOUS_HOLD_THRESHOLD: (ACTION_HOLD_BOTH,),
      whichever button went down first

    Both buttons pressed in the same step have no order, so a quick release
    of both returns no action.
    """

    def __init__(self, buttons: tuple[str, str]):
        """Initialize the state machine.

        :param buttons: The two button names
        """
        self._buttons = buttons
        self._pressed = {b: False for b in buttons}
        self._down = {b: False for b in buttons}
        self._state = _STATE_IDLE
        self._held: str | None = None
        self._chord_used = False
        self._both_down_since = 0.0

    @property
    def is_idle(self) -> bool:
        """True when no gesture is in progress."""
        return self._state == _STATE_IDLE

    def step(self, events: list[tuple[str, bool]], now: float) -> tuple | None:
        """Apply events and advance the state machine by one transition.

        :param events: (button, pressed) pairs that arrived since the last step
        :param now: Current time in seconds
        :return: An action tuple, or None
        """
        for button, pressed in events:
            if pressed:
                self._pressed[button] = True
            self._down[button] = pressed

        if self._state == _STATE_IDLE:
            return self._step_idle(now)
        if self._state == _STATE_SINGLE_HELD:
            return self._step_single_held(now)
        if self._state == _STATE_BOTH_DOWN:
            return self._step_both_down(now)
        return self._step_wait_release()

    def _other(self, button: str) -> str:
        return self._buttons[1] if button == self._buttons[0] else self._buttons[0]

    def _step_idle(self, now: float) -> None:
        new_presses = [b for b in self._buttons if self._pressed[b]]
        for b in new_presses:
            self._pressed[b] = False
        if len(new_presses) == 2:
            self._held = None
            self._state = _STATE_BOTH_DOWN
            self._both_down_since = now
        elif len(new_presses) == 1:
            self._held = new_presses[0]
            self._chord_used = False
            self._state = _STATE_SINGLE_HELD

    def _step_single_held(self, now: float) -> tuple | None:
        held = self._held
        assert held is not None
        other = self._other(held)
        if self._pressed[other]:
            self._pressed[other] = False
            self._state = _STATE_BOTH_DOWN
            self._both_down_since = now
            return None
        if not self._down[held]:
            self._state = _STATE_IDLE
            self._held = None
            if not self._chord_used:
                return (ACTION_SINGLE, held)
        return None

    def _step_both_down(self, now: float) -> tuple | None:
        if not all(self._down.values()):
            self._state = _STATE_WAIT_RELEASE
            if self._held is not None:
                self._chord_used = True
                return (ACTION_CHORD, self._held, self._other(self._held))
            return None
        if now - self._both_down_since >= SIMULTANEOUS_HOLD_THRESHOLD:
            self._held = None
            self._state = _STATE_WAIT_RELEASE
            return (ACTION_HOLD_BOTH,)
        return None

    def _step_wait_release(self) -> None:
        for b in self._buttons:
            self._pressed[b] = False
        if not any(self._down.values()):
            self._state = _STATE_IDLE
            self._held = None
        elif self._held is not None and self._down[self._held]:
            self._state = _STATE_SINGLE_HELD
