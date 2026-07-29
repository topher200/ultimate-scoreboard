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
        class _EnumMeta(type):
            """Metaclass for Enum stub that converts class attributes to enum members."""

            def __new__(mcs, name, bases, namespace):
                """Create enum class and convert attributes to members."""
                # Remove special attributes
                members = {}
                for key, value in list(namespace.items()):
                    if not key.startswith("_") and not callable(value):
                        members[key] = value
                        del namespace[key]

                # Create the class
                cls = super().__new__(mcs, name, bases, namespace)

                # Create enum members
                for member_name, member_value in members.items():
                    member = cls(member_value)
                    member.name = member_name
                    setattr(cls, member_name, member)

                return cls

        class Enum:
            """Stub Enum class for CircuitPython compatibility."""

            __metaclass__ = _EnumMeta

            def __init__(self, value):
                """Initialize enum member with a value."""
                self.value = value
                self.name = None

            def __repr__(self):
                """Return string representation of enum member."""
                if self.name:
                    return f"<{self.__class__.__name__}.{self.name}: {self.value!r}>"
                return f"<{self.__class__.__name__}: {self.value!r}>"

            def __eq__(self, other):
                """Check equality with another enum member."""
                if isinstance(other, self.__class__):
                    return self.value == other.value
                return False

            def __hash__(self):
                """Make enum members hashable."""
                return hash((self.__class__, self.value))


__all__ = [
    "Callable",
    "Any",
    "NamedTuple",
    "Protocol",
    "TYPE_CHECKING",
    "Enum",
]
