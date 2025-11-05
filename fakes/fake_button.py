"""Fake button implementation for testing without hardware."""


class FakeButton:
    """Fake implementation of digitalio.DigitalInOut for button testing.

    Buttons are active-low: value is False when pressed, True when released.
    """

    def __init__(self):
        """Initialize a fake button in released state (value=True)."""
        self._value = True

    @property
    def value(self):
        """Get the button state.

        :return: True if button is released, False if pressed (active-low)
        """
        return self._value

    @value.setter
    def value(self, state):
        """Set the button state for testing.

        :param state: True for released, False for pressed (active-low)
        """
        self._value = state

    def press(self):
        """Helper method to simulate a button press."""
        self._value = False

    def release(self):
        """Helper method to simulate a button release."""
        self._value = True
