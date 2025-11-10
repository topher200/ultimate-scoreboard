"""Protocol definitions for type checking interfaces.

This allows both the real CircuitPython modules and mock CircuitPython modules
to be used interchangeably in type-checked code.
"""

from src.protocols.board import BoardLike
from src.protocols.button import ButtonLike
from src.protocols.keypad import EventLike, EventQueueLike, KeysLike
from src.protocols.matrixportal import MatrixPortalLike

__all__ = [
    "BoardLike",
    "ButtonLike",
    "EventLike",
    "EventQueueLike",
    "KeysLike",
    "MatrixPortalLike",
]
