"""Manages hardware interactions like button presses."""

import asyncio
import time

import keypad

from src.button_state_machine import (
    ACTION_CHORD,
    ACTION_HOLD_BOTH,
    ACTION_SINGLE,
    ButtonStateMachine,
)
from src.compat import Callable
from src.protocols import BoardLike, KeysLike

# Button name constants
BUTTON_LEFT = "left"
BUTTON_RIGHT = "right"

# Key number constants (from keypad events)
# Pin order: (board.A1, board.A3) means LEFT=0, RIGHT=1
KEY_NUMBER_BUTTON_LEFT = 0
KEY_NUMBER_BUTTON_RIGHT = 1

# Polling rates for button monitoring loop
BUTTON_POLLING_RATE_IDLE = 0.1
BUTTON_POLLING_RATE_ACTIVE = 0.02

# Map key_number (from keypad events) to button names
KEY_NUMBER_TO_BUTTON = {
    KEY_NUMBER_BUTTON_LEFT: BUTTON_LEFT,
    KEY_NUMBER_BUTTON_RIGHT: BUTTON_RIGHT,
}


def create_keys_from_board(board: BoardLike) -> KeysLike:
    """Create configured keypad.Keys object from board configuration.

    :param board: Board module (or BoardLike object) containing button pin definitions
    :return: Configured keypad.Keys object
    """
    return keypad.Keys(
        (board.A1, board.A3),
        value_when_pressed=False,  # Active-low (button connects to ground)
        pull=True,  # Enable internal pull-ups
    )


class HardwareManager:
    """Runs button callbacks for the gestures that ButtonStateMachine recognizes.

    Uses keypad.Keys for hardware-level debouncing and event-based key press detection.
    """

    def __init__(self, keys: KeysLike, get_time: Callable = time.monotonic):
        """Initialize HardwareManager with keypad.Keys configuration.

        :param keys: keypad.Keys object (or KeysLike protocol implementation)
        :param get_time: Callable returning current time in seconds
        """
        self._keys = keys
        self._get_time = get_time

    def _read_events(self) -> list[tuple[str, bool]]:
        """Drain the keypad event queue into (button, pressed) pairs."""
        events = []
        while True:
            event = self._keys.events.get()
            if event is None:
                return events
            button_name = KEY_NUMBER_TO_BUTTON.get(event.key_number)
            if button_name is not None:
                events.append((button_name, event.pressed))

    async def monitor_buttons(
        self,
        callbacks: dict[str, Callable],
        hold_both_callback: Callable | None = None,
        chord_callbacks: dict[tuple[str, str], Callable] | None = None,
        long_hold_both_callback: Callable | None = None,
    ) -> None:
        """Monitor button presses and call registered callbacks.

        See ButtonStateMachine for which gesture fires which callback.

        :param callbacks: Dictionary mapping button names to async callbacks for
            single presses.
        :param hold_both_callback: Optional async callback for holding both buttons.
        :param chord_callbacks: Optional dictionary mapping (held_button, tapped_button)
            tuples to async callbacks.
        :param long_hold_both_callback: Optional async callback for holding both
            buttons longer.
        """
        if chord_callbacks is None:
            chord_callbacks = {}
        machine = ButtonStateMachine((BUTTON_LEFT, BUTTON_RIGHT))

        while True:
            action = machine.step(self._read_events(), self._get_time())
            if action is not None:
                if action[0] == ACTION_SINGLE:
                    callback = callbacks.get(action[1])
                elif action[0] == ACTION_CHORD:
                    callback = chord_callbacks.get((action[1], action[2]))
                elif action[0] == ACTION_HOLD_BOTH:
                    callback = hold_both_callback
                else:
                    callback = long_hold_both_callback
                if callback is not None:
                    await callback()

            await asyncio.sleep(
                BUTTON_POLLING_RATE_IDLE
                if machine.is_idle
                else BUTTON_POLLING_RATE_ACTIVE
            )
