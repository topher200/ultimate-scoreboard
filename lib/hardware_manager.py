"""Manages hardware interactions like button presses."""

import asyncio
from collections.abc import Callable

import digitalio

from lib.protocols import BoardLike, ButtonLike

# Button name constants
BUTTON_UP = "up"
BUTTON_DOWN = "down"

# Polling rate for button monitoring loop
BUTTON_POLLING_RATE = 0.1


def create_buttons_from_board(board: BoardLike) -> dict[str, ButtonLike]:
    """Create configured button objects from board configuration.

    :param board: Board module (or BoardLike object) containing button pin definitions
    :return: Dictionary mapping button names to configured button objects
    """
    button_up = digitalio.DigitalInOut(board.BUTTON_UP)
    button_up.direction = digitalio.Direction.INPUT
    button_up.pull = digitalio.Pull.UP

    button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
    button_down.direction = digitalio.Direction.INPUT
    button_down.pull = digitalio.Pull.UP

    return {
        BUTTON_UP: button_up,
        BUTTON_DOWN: button_down,
    }


class HardwareManager:
    """Manages button state detection with debouncing.

    Buttons are active-low: button.value is False when pressed, True when released.
    """

    def __init__(self, buttons: dict[str, ButtonLike]):
        """Initialize HardwareManager with button configuration.

        :param buttons: Dictionary mapping button names to button objects
                       e.g., {BUTTON_UP: button_up_obj, BUTTON_DOWN: button_down_obj}
        """
        self._buttons = buttons
        # Track if button was pressed in previous update (for edge detection)
        self._button_was_pressed = {name: False for name in buttons.keys()}
        # Track if there's a pending press event to report
        self._button_press_event = {name: False for name in buttons.keys()}

    def update(self) -> None:
        """Update internal button state by checking all buttons.

        Call this method once per main loop iteration to check button states
        and update debouncing tracking.
        """
        for name, button in self._buttons.items():
            # Buttons are active-low, so pressed = not button.value
            if not button.value and not self._button_was_pressed[name]:
                # Button just pressed (rising edge) - create a press event
                self._button_was_pressed[name] = True
                self._button_press_event[name] = True
            elif button.value:
                # Button released, reset state
                self._button_was_pressed[name] = False

    def is_button_pressed(self, button_name: str) -> bool:
        """Check if a button was just pressed (rising edge detection).

        Returns True once per button press, then False until released and pressed again.
        Must call update() before checking button states.

        :param button_name: Name of the button to check
        :return: True if button was just pressed, False otherwise
        :raises KeyError: If button_name is not configured
        """
        if button_name not in self._buttons:
            raise KeyError(f"Unknown button name: {button_name}")

        # Check if there's a pending press event
        if self._button_press_event[button_name]:
            # Consume the event and return True
            self._button_press_event[button_name] = False
            return True
        return False

    async def monitor_buttons(self, callbacks: dict[str, Callable]) -> None:
        """Monitor button presses and call registered callbacks.

        Runs an infinite loop checking for button presses and calling the
        appropriate async callback function when a button is pressed.

        :param callbacks: Dictionary mapping button names to async callback functions
        """
        while True:
            self.update()

            for button_name, callback in callbacks.items():
                if self.is_button_pressed(button_name):
                    await callback()

            await asyncio.sleep(BUTTON_POLLING_RATE)
