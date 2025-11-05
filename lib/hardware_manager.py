"""Manages hardware interactions like button presses."""


class HardwareManager:
    """Manages button state detection with debouncing.

    Buttons are active-low: button.value is False when pressed, True when released.
    """

    def __init__(self, buttons: dict):
        """Initialize HardwareManager with button configuration.

        :param buttons: Dictionary mapping button names to button objects
                       e.g., {"up": button_up_obj, "down": button_down_obj}
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
