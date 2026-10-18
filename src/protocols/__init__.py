"""Protocol definitions for type checking interfaces.

This allows both the real CircuitPython modules and mock CircuitPython modules
to be used interchangeably in type-checked code.
"""

from src.protocols.board import BoardLike
from src.protocols.http import HttpLike, ResponseLike
from src.protocols.keypad import EventLike, EventQueueLike, KeysLike
from src.protocols.matrixportal import MatrixPortalLike
from src.protocols.network import NetworkLike, WebServerLike

__all__ = [
    "BoardLike",
    "EventLike",
    "EventQueueLike",
    "HttpLike",
    "KeysLike",
    "MatrixPortalLike",
    "NetworkLike",
    "ResponseLike",
    "WebServerLike",
]
