"""Fake keypad implementation for testing without hardware."""


class FakeEvent:
    """Fake keypad event object."""

    def __init__(self, key_number: int, pressed: bool):
        """Initialize a fake event.

        :param key_number: The key number (0-indexed)
        :param pressed: True if key was pressed, False if released
        """
        self.key_number = key_number
        self.pressed = pressed


class FakeEventQueue:
    """Fake event queue that mimics keypad.Keys.events."""

    def __init__(self):
        """Initialize an empty event queue."""
        self._events = []

    def get(self):
        """Get the next event from the queue.

        :return: Event object if available, None otherwise
        """
        if self._events:
            return self._events.pop(0)
        return None

    def push(self, key_number: int, pressed: bool):
        """Add an event to the queue for testing.

        :param key_number: The key number (0-indexed)
        :param pressed: True if key was pressed, False if released
        """
        self._events.append(FakeEvent(key_number, pressed))


class FakeKeys:
    """Fake implementation of keypad.Keys for button testing.

    Mimics the keypad.Keys API with an event queue.
    """

    def __init__(self, pins: tuple, value_when_pressed: bool = False, pull: bool = True):
        """Initialize fake keys.

        :param pins: Tuple of pin objects (not used in fake, but kept for API compatibility)
        :param value_when_pressed: Value when pressed (not used in fake)
        :param pull: Whether pull-up is enabled (not used in fake)
        """
        self._pins = pins
        self._value_when_pressed = value_when_pressed
        self._pull = pull
        self.events = FakeEventQueue()

    def press_key(self, key_number: int):
        """Helper method to simulate a key press.

        :param key_number: The key number (0-indexed) to press
        """
        self.events.push(key_number, True)

    def release_key(self, key_number: int):
        """Helper method to simulate a key release.

        :param key_number: The key number (0-indexed) to release
        """
        self.events.push(key_number, False)

