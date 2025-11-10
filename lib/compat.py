"""Compatibility layer for imports not available in CircuitPython.

This module provides a centralized location for handling imports that work in
standard Python but are unavailable or have different locations in CircuitPython.
"""

try:
    from collections.abc import Callable as _Callable
    from typing import TYPE_CHECKING
    from typing import Any as _Any
    from typing import Protocol as _Protocol
except ImportError:
    TYPE_CHECKING = False

    # CircuitPython compatibility: create stub classes when typing is unavailable
    class _Callable:
        """Stub Callable class for CircuitPython compatibility."""

    class _Protocol:
        """Stub Protocol class for CircuitPython compatibility."""

    # Any needs to be a class (not instance) that can be used in type annotations
    # and supports union operations
    class _Any:
        """Stub Any class for CircuitPython compatibility."""

        def __or__(self, other):
            return _UnionStub(self, other)

        def __ror__(self, other):
            return _UnionStub(other, self)

    class _UnionStub:
        """Stub for union types like Any | None."""

        def __init__(self, left, right):
            self.left = left
            self.right = right


# Export the appropriate types based on whether typing is available
if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Protocol
else:
    Callable = _Callable
    Any = _Any
    Protocol = _Protocol

__all__ = ["Callable", "Any", "Protocol", "TYPE_CHECKING"]
