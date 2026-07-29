"""Compatibility layer for imports not available in CircuitPython.

This module provides a centralized location for handling imports that work in
standard Python but are unavailable or have different locations in CircuitPython.
"""

try:
    from collections.abc import Callable as _Callable
    from typing import TYPE_CHECKING
    from typing import Any as _Any
    from typing import NamedTuple as _NamedTuple
    from typing import Protocol as _Protocol
except ImportError:
    TYPE_CHECKING = False

    # CircuitPython compatibility: create stub classes when typing is unavailable
    class _Callable:
        """Stub Callable class for CircuitPython compatibility."""

    class _Protocol:
        """Stub Protocol class for CircuitPython compatibility."""

    # NamedTuple stub for CircuitPython compatibility
    class _NamedTuple:
        """Stub NamedTuple base class for CircuitPython compatibility."""

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    # Any needs to be a class (not instance) so it can be used in annotations
    class _Any:
        """Stub Any class for CircuitPython compatibility."""


# Export the appropriate types based on whether typing is available
if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, NamedTuple, Protocol
else:
    Callable = _Callable
    Any = _Any
    NamedTuple = _NamedTuple
    Protocol = _Protocol


# Export Enum (available in standard Python, stub in CircuitPython)
# For type checking, use real enum import (handled above in TYPE_CHECKING block)
# For runtime, try to import from enum, fall back to stub if unavailable
if TYPE_CHECKING:
    from enum import Enum
else:
    try:
        from enum import Enum
    except ImportError:
        # CircuitPython compatibility: create stub Enum class when enum is unavailable
        class Enum:
            """Stub Enum base class for CircuitPython compatibility.

            Subclass attributes keep their plain values.
            """


__all__ = [
    "Callable",
    "Any",
    "NamedTuple",
    "Protocol",
    "TYPE_CHECKING",
    "Enum",
]
