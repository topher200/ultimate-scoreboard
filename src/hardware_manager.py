"""Manages hardware interactions like button presses."""

import asyncio
import time

import keypad

from src.compat import Callable
from src.protocols import BoardLike, KeysLike

# Button name constants
BUTTON_UP = "up"
BUTTON_DOWN = "down"
BUTTON_LEFT = "left"
BUTTON_RIGHT = "right"

# Key number constants (from keypad events)
# Pin order: (board.BUTTON_UP, board.BUTTON_DOWN, board.A1, board.A3)
# means UP=0, DOWN=1, LEFT=2, RIGHT=3
KEY_NUMBER_BUTTON_UP = 0
KEY_NUMBER_BUTTON_DOWN = 1
KEY_NUMBER_BUTTON_LEFT = 2
KEY_NUMBER_BUTTON_RIGHT = 3

# Polling rate for button monitoring loop
BUTTON_POLLING_RATE = 0.1

# Hold threshold for long simultaneous press (seconds)
SIMULTANEOUS_HOLD_THRESHOLD = 1.0

# Map key_number (from keypad events) to button names
KEY_NUMBER_TO_BUTTON = {
    KEY_NUMBER_BUTTON_UP: BUTTON_UP,
    KEY_NUMBER_BUTTON_DOWN: BUTTON_DOWN,
    KEY_NUMBER_BUTTON_LEFT: BUTTON_LEFT,
    KEY_NUMBER_BUTTON_RIGHT: BUTTON_RIGHT,
}


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


class _HoldState:
    """Tracks state during a simultaneous hold detection."""

    def __init__(
        self,
        pair: tuple[str, str],
        short_cb: Callable,
        long_cb: Callable,
        press_time: float,
    ):
        self.pair = pair
        self.short_cb = short_cb
        self.long_cb = long_cb
        self.press_time = press_time
        self.long_fired = False


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
            BUTTON_UP: False,
            BUTTON_DOWN: False,
            BUTTON_LEFT: False,
            BUTTON_RIGHT: False,
        }
        # Track pending release events by button name
        self._button_release_event = {
            BUTTON_UP: False,
            BUTTON_DOWN: False,
            BUTTON_LEFT: False,
            BUTTON_RIGHT: False,
        }

    def update(self) -> None:
        """Update internal button state by processing keypad events.

        Call this method once per main loop iteration to process events
        from the keypad event queue. Only processes key press events (ignores releases).
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
                else:
                    self._button_release_event[button_name] = True

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

        # Check if there's a pending press event
        if self._button_press_event[button_name]:
            # Consume the event and return True
            self._button_press_event[button_name] = False
            return True
        return False

    def are_buttons_pressed_simultaneously(self, button1: str, button2: str) -> bool:
        """Check if two buttons are both pressed simultaneously.

        Checks if both buttons have pending press events without consuming them.
        Must call update() before checking button states.

        :param button1: Name of the first button to check
        :param button2: Name of the second button to check
        :return: True if both buttons have pending press events, False otherwise
        :raises KeyError: If either button_name is not configured
        """
        if button1 not in self._button_press_event:
            raise KeyError(f"Unknown button name: {button1}")
        if button2 not in self._button_press_event:
            raise KeyError(f"Unknown button name: {button2}")

        return (
            self._button_press_event[button1] and self._button_press_event[button2]
        )

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

        Sets the pending press event flag to False for the specified buttons.
        This is used to prevent individual button handlers from firing when
        a simultaneous press is detected.

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
        simultaneous_callbacks: dict[tuple[str, str], Callable] | None = None,
        long_simultaneous_callbacks: dict[tuple[str, str], Callable] | None = None,
    ) -> None:
        """Monitor button presses and call registered callbacks.

        Runs an infinite loop processing keypad events and calling the
        appropriate async callback function when a button is pressed.
        Simultaneous button presses are checked first and take precedence
        over individual button handlers.

        When long_simultaneous_callbacks is provided for a button pair, the system
        distinguishes between short and long simultaneous presses:
        - Short press (released before SIMULTANEOUS_HOLD_THRESHOLD): fires the
          simultaneous_callbacks entry (e.g. undo)
        - Long hold (held >= SIMULTANEOUS_HOLD_THRESHOLD): fires the
          long_simultaneous_callbacks entry (e.g. toggle gender)

        :param callbacks: Dictionary mapping button names to async callback functions
        :param simultaneous_callbacks: Optional dictionary mapping button pairs
            (tuple of two button names) to async callback functions for simultaneous presses.
        :param long_simultaneous_callbacks: Optional dictionary mapping button pairs
            to async callback functions for long simultaneous holds.
        """
        if simultaneous_callbacks is None:
            simultaneous_callbacks = {}
        if long_simultaneous_callbacks is None:
            long_simultaneous_callbacks = {}

        hold_state: _HoldState | None = None

        while True:
            self.update()

            if hold_state is None:
                # NORMAL MODE: check simultaneous presses
                simultaneous_handled = False
                for (button1, button2), callback in simultaneous_callbacks.items():
                    if self.are_buttons_pressed_simultaneously(button1, button2):
                        self.consume_button_events(button1, button2)
                        long_cb = long_simultaneous_callbacks.get((button1, button2))
                        if long_cb is not None:
                            # Enter hold-detection mode
                            hold_state = _HoldState(
                                pair=(button1, button2),
                                short_cb=callback,
                                long_cb=long_cb,
                                press_time=self._get_time(),
                            )
                        else:
                            # No long callback — fire immediately (existing behavior)
                            await callback()
                        simultaneous_handled = True
                        break

                if not simultaneous_handled:
                    for button_name, callback in callbacks.items():
                        if self.is_button_pressed(button_name):
                            await callback()

            elif not hold_state.long_fired:
                # HOLD-DETECTION MODE: waiting to see if short or long
                b1, b2 = hold_state.pair
                elapsed = self._get_time() - hold_state.press_time

                released = (
                    self.is_button_released(b1) or self.is_button_released(b2)
                )
                if released:
                    self.consume_release_events(b1, b2)
                    await hold_state.short_cb()
                    hold_state = None
                elif elapsed >= SIMULTANEOUS_HOLD_THRESHOLD:
                    await hold_state.long_cb()
                    hold_state.long_fired = True

            else:
                # POST-LONG-FIRE MODE: wait for buttons to be released
                b1, b2 = hold_state.pair
                released = (
                    self.is_button_released(b1) or self.is_button_released(b2)
                )
                if released:
                    self.consume_release_events(b1, b2)
                    hold_state = None

            # Consume stray press/release events during hold states
            if hold_state is not None:
                b1, b2 = hold_state.pair
                self.consume_button_events(b1, b2)
                self.consume_release_events(b1, b2)

            await asyncio.sleep(BUTTON_POLLING_RATE)
