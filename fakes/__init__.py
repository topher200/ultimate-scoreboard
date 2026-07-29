"""Fake implementations for testing without hardware."""

from .fake_button import FakeButton
from .fake_displayio import FakeGroup
from .fake_keypad import FakeKeys
from .fake_label import FakeLabel
from .fake_matrixportal import FakeDisplay, FakeMatrixPortal

# Provide a fake FONT constant for terminalio.FONT
FakeTerminalio = type("FakeTerminalio", (), {"FONT": object()})()

__all__ = [
    "FakeMatrixPortal",
    "FakeDisplay",
    "FakeGroup",
    "FakeLabel",
    "FakeTerminalio",
    "FakeButton",
    "FakeKeys",
]
