"""Manages hardware interactions like button presses."""

import asyncio

import keypad

from src.compat import Callable
from src.protocols import BoardLike, KeysLike

# Button name constants
BUTTON_UP = "up"
BUTTON_DOWN = "down"

# Key number constants (from keypad events)
# Pin order: (board.BUTTON_UP, board.BUTTON_DOWN) means UP=0, DOWN=1
KEY_NUMBER_BUTTON_UP = 0
KEY_NUMBER_BUTTON_DOWN = 1

# Polling rate for button monitoring loop
BUTTON_POLLING_RATE = 0.1

# Map key_number (from keypad events) to button names
KEY_NUMBER_TO_BUTTON = {
    KEY_NUMBER_BUTTON_UP: BUTTON_UP,
    KEY_NUMBER_BUTTON_DOWN: BUTTON_DOWN,
}


def create_keys_from_board(board: BoardLike) -> KeysLike:
    """Create configured keypad.Keys object from board configuration.

    :param board: Board module (or BoardLike object) containing button pin definitions
    :return: Configured keypad.Keys object
    """
    return keypad.Keys(
        (board.BUTTON_UP, board.BUTTON_DOWN),
        value_when_pressed=False,  # Active-low (button connects to ground)
        pull=True,  # Enable internal pull-ups
    )


class HardwareManager:
    """Manages button state detection using keypad library with automatic debouncing.

    Uses keypad.Keys for hardware-level debouncing and event-based key press detection.
    """

    def __init__(self, keys: KeysLike):
        """Initialize HardwareManager with keypad.Keys configuration.

        :param keys: keypad.Keys object (or KeysLike protocol implementation)
        """
        self._keys = keys
        # Track pending press events by button name
        self._button_press_event = {
            BUTTON_UP: False,
            BUTTON_DOWN: False,
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

            # Only process press events, ignore releases
            if event.pressed:
                # Map key_number to button name
                button_name = KEY_NUMBER_TO_BUTTON.get(event.key_number)
                if button_name is not None:
                    self._button_press_event[button_name] = True

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

    async def monitor_buttons(self, callbacks: dict[str, Callable]) -> None:
        """Monitor button presses and call registered callbacks.

        Runs an infinite loop processing keypad events and calling the
        appropriate async callback function when a button is pressed.

        :param callbacks: Dictionary mapping button names to async callback functions
        """
        while True:
            # Process all available events from the queue
            self.update()

            # Check for button presses and call callbacks
            for button_name, callback in callbacks.items():
                if self.is_button_pressed(button_name):
                    await callback()

            # Brief sleep to avoid tight loop
            await asyncio.sleep(BUTTON_POLLING_RATE)
