"""Manages hardware interactions like button presses."""

import asyncio
import time

import keypad

from src.compat import Callable
from src.protocols import BoardLike, KeysLike

# Button name constants
BUTTON_LEFT = "left"
BUTTON_RIGHT = "right"

# Key number constants (from keypad events)
# Pin order: (board.BUTTON_UP, board.BUTTON_DOWN, board.A1, board.A3)
# means UP=0, DOWN=1, LEFT=2, RIGHT=3
KEY_NUMBER_BUTTON_LEFT = 2
KEY_NUMBER_BUTTON_RIGHT = 3

# Polling rates for button monitoring loop
BUTTON_POLLING_RATE_IDLE = 0.1
BUTTON_POLLING_RATE_ACTIVE = 0.02

# Hold threshold for long simultaneous press (seconds)
SIMULTANEOUS_HOLD_THRESHOLD = 1.0

# Map key_number (from keypad events) to button names
KEY_NUMBER_TO_BUTTON = {
    KEY_NUMBER_BUTTON_LEFT: BUTTON_LEFT,
    KEY_NUMBER_BUTTON_RIGHT: BUTTON_RIGHT,
}

# State machine states
_STATE_IDLE = "idle"
_STATE_SINGLE_HELD = "single_held"
_STATE_BOTH_HELD = "both_held"
_STATE_WAIT_RELEASE = "wait_release"


def create_keys_from_board(board: BoardLike) -> KeysLike:
    """Create configured keypad.Keys object from board configuration.

    :param board: Board module (or BoardLike object) containing button pin definitions
    :return: Configured keypad.Keys object
    """
    return keypad.Keys(
        (board.BUTTON_UP, board.BUTTON_DOWN, board.A1, board.A3),
        value_when_pressed=False,  # Active-low (button connects to ground)
        pull=True,  # Enable internal pull-ups
    )


class HardwareManager:
    """Manages button state detection using keypad library with automatic debouncing.

    Uses keypad.Keys for hardware-level debouncing and event-based key press detection.
    """

    def __init__(self, keys: KeysLike, get_time: Callable = time.monotonic):
        """Initialize HardwareManager with keypad.Keys configuration.

        :param keys: keypad.Keys object (or KeysLike protocol implementation)
        :param get_time: Callable returning current time in seconds (default: time.monotonic)
        """
        self._keys = keys
        self._get_time = get_time
        # Track pending press events by button name
        self._button_press_event = {
            BUTTON_LEFT: False,
            BUTTON_RIGHT: False,
        }
        # Track pending release events by button name
        self._button_release_event = {
            BUTTON_LEFT: False,
            BUTTON_RIGHT: False,
        }
        # Track physical button state (True = currently held down)
        self._button_is_down = {
            BUTTON_LEFT: False,
            BUTTON_RIGHT: False,
        }

    def update(self) -> None:
        """Update internal button state by processing keypad events.

        Call this method once per main loop iteration to process events
        from the keypad event queue.
        """
        # Process all available events from the queue
        while True:
            event = self._keys.events.get()
            if event is None:
                break

            # Map key_number to button name
            button_name = KEY_NUMBER_TO_BUTTON.get(event.key_number)
            if button_name is not None:
                if event.pressed:
                    self._button_press_event[button_name] = True
                    self._button_is_down[button_name] = True
                else:
                    self._button_release_event[button_name] = True
                    self._button_is_down[button_name] = False

    def is_button_pressed(self, button_name: str) -> bool:
        """Check if a button was just pressed (edge detection).

        Returns True once per button press, then False until the next press.
        Must call update() before checking button states.

        :param button_name: Name of the button to check
        :return: True if button was just pressed, False otherwise
        :raises KeyError: If button_name is not configured
        """
        if button_name not in self._button_press_event:
            raise KeyError(f"Unknown button name: {button_name}")

        if self._button_press_event[button_name]:
            self._button_press_event[button_name] = False
            return True
        return False

    def is_button_released(self, button_name: str) -> bool:
        """Check if a button was just released (edge detection).

        Returns True once per button release, then False until the next release.
        Must call update() before checking button states.

        :param button_name: Name of the button to check
        :return: True if button was just released, False otherwise
        :raises KeyError: If button_name is not configured
        """
        if button_name not in self._button_release_event:
            raise KeyError(f"Unknown button name: {button_name}")

        if self._button_release_event[button_name]:
            self._button_release_event[button_name] = False
            return True
        return False

    def consume_release_events(self, *button_names: str) -> None:
        """Consume release events for one or more buttons.

        :param button_names: One or more button names to consume release events for
        :raises KeyError: If any button_name is not configured
        """
        for button_name in button_names:
            if button_name not in self._button_release_event:
                raise KeyError(f"Unknown button name: {button_name}")
            self._button_release_event[button_name] = False

    def consume_button_events(self, *button_names: str) -> None:
        """Consume press events for one or more buttons.

        :param button_names: One or more button names to consume events for
        :raises KeyError: If any button_name is not configured
        """
        for button_name in button_names:
            if button_name not in self._button_press_event:
                raise KeyError(f"Unknown button name: {button_name}")
            self._button_press_event[button_name] = False

    async def monitor_buttons(
        self,
        callbacks: dict[str, Callable],
        hold_both_callback: Callable | None = None,
        chord_callbacks: dict[tuple[str, str], Callable] | None = None,
    ) -> None:
        """Monitor button presses and call registered callbacks.

        Uses a state machine to distinguish between individual presses, chords
        (hold one button then press the other), and simultaneous holds:

        - Individual press: fires on release if no chord was detected
        - Chord (hold A, press B): fires the chord_callbacks[(A, B)] entry
        - Both held ~1s: fires hold_both_callback (e.g. reset)

        :param callbacks: Dictionary mapping button names to async callback functions.
            Individual callbacks fire on button release if no chord was detected.
        :param hold_both_callback: Optional async callback for when both buttons
            are held simultaneously for SIMULTANEOUS_HOLD_THRESHOLD seconds.
        :param chord_callbacks: Optional dictionary mapping (held_button, pressed_button)
            tuples to async callback functions. Fires when one button is held and
            the other is pressed in a subsequent update cycle.
        """
        if chord_callbacks is None:
            chord_callbacks = {}

        state = _STATE_IDLE
        held_button: str | None = None
        chord_used = False  # True if a chord fired during this hold
        press_time = 0.0
        button_names = list(callbacks.keys())

        while True:
            self.update()

            if state == _STATE_IDLE:
                # Check for new button presses
                new_presses = [
                    b for b in button_names if self._button_press_event.get(b, False)
                ]

                if len(new_presses) >= 2:
                    # Both pressed in same update cycle → simultaneous hold
                    for b in new_presses:
                        self.consume_button_events(b)
                    state = _STATE_BOTH_HELD
                    press_time = self._get_time()
                elif len(new_presses) == 1:
                    held_button = new_presses[0]
                    chord_used = False
                    self.consume_button_events(held_button)
                    state = _STATE_SINGLE_HELD
                    press_time = self._get_time()

            elif state == _STATE_SINGLE_HELD:
                assert held_button is not None
                # Check if the other button was pressed (chord)
                other_pressed = None
                for b in button_names:
                    if b != held_button and self._button_press_event.get(b, False):
                        other_pressed = b
                        break

                if other_pressed is not None:
                    self.consume_button_events(other_pressed)
                    chord_cb = chord_callbacks.get((held_button, other_pressed))
                    if chord_cb is not None:
                        await chord_cb()
                    chord_used = True
                    # Keep held_button so WAIT_RELEASE can return to
                    # SINGLE_HELD for repeated chords (e.g. hold RIGHT,
                    # tap LEFT multiple times to undo)
                    state = _STATE_WAIT_RELEASE
                elif not self._button_is_down.get(held_button, True):
                    # Held button physically released — use _button_is_down
                    # instead of release events to avoid stale-event bugs
                    if not chord_used:
                        # Released without any chord → fire individual callback
                        cb = callbacks.get(held_button)
                        if cb is not None:
                            await cb()
                    state = _STATE_IDLE
                    held_button = None

            elif state == _STATE_BOTH_HELD:
                elapsed = self._get_time() - press_time
                any_released = any(
                    not self._button_is_down.get(b, True) for b in button_names
                )

                if any_released:
                    # Aborted hold — no action
                    state = _STATE_IDLE
                elif elapsed >= SIMULTANEOUS_HOLD_THRESHOLD:
                    if hold_both_callback is not None:
                        await hold_both_callback()
                    state = _STATE_WAIT_RELEASE

            elif state == _STATE_WAIT_RELEASE:
                # Consume stray press events to prevent false chord detection
                for b in button_names:
                    self.consume_button_events(b)

                all_up = all(
                    not self._button_is_down.get(b, False) for b in button_names
                )
                if all_up:
                    state = _STATE_IDLE
                    held_button = None
                elif (
                    held_button is not None
                    and self._button_is_down.get(held_button, False)
                ):
                    # The original held button is still down — return to
                    # SINGLE_HELD so the user can tap the other button
                    # again for repeated chords (e.g. multiple undos)
                    state = _STATE_SINGLE_HELD

            poll_rate = (
                BUTTON_POLLING_RATE_IDLE
                if state == _STATE_IDLE
                else BUTTON_POLLING_RATE_ACTIVE
            )
            await asyncio.sleep(poll_rate)
