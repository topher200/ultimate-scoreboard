"""Protocol definitions for keypad interfaces."""

from src.compat import Protocol


class EventLike(Protocol):
    """Protocol defining the keypad event interface."""

    key_number: int
    """The key number (0-indexed) that generated this event."""

    pressed: bool
    """True if key was pressed, False if released."""


class EventQueueLike(Protocol):
    """Protocol defining the keypad event queue interface."""

    def get(self) -> EventLike | None:
        """Get the next event from the queue.

        :return: Event object if available, None otherwise
        """
        ...


class KeysLike(Protocol):
    """Protocol defining the keypad.Keys interface used in this project."""

    @property
    def events(self) -> EventQueueLike:
        """Get the event queue for key events."""
        ...

