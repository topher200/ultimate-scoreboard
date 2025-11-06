"""Type stubs for CircuitPython digitalio module.

This module provides digital input/output functionality for CircuitPython.
"""

from typing import Any

class _Direction:
    """Pin direction constants."""

    INPUT: int
    OUTPUT: int

class _Pull:
    """Pull resistor configuration constants."""

    UP: int
    DOWN: int

# Module-level constants
Direction: _Direction
Pull: _Pull

class DigitalInOut:
    """Digital input/output pin control."""

    def __init__(self, pin: Any) -> None:
        """Initialize a digital pin.

        :param pin: The pin to control (from board module)
        """
        ...

    @property
    def direction(self) -> int:
        """Get the pin direction."""
        ...

    @direction.setter
    def direction(self, value: int) -> None:
        """Set the pin direction."""
        ...

    @property
    def pull(self) -> int | None:
        """Get the pull resistor configuration."""
        ...

    @pull.setter
    def pull(self, value: int | None) -> None:
        """Set the pull resistor configuration."""
        ...

    @property
    def value(self) -> bool:
        """Get the pin value."""
        ...

    @value.setter
    def value(self, val: bool) -> None:
        """Set the pin value."""
        ...
