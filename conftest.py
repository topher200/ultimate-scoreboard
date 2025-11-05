"""Pytest configuration and fixtures for mocking CircuitPython modules."""

import asyncio
import sys
from unittest.mock import MagicMock

import pytest

from fakes import FakeGroup, FakeLabel, FakeTerminalio

# Mock CircuitPython-specific modules that don't exist in regular Python
# These must be mocked before any imports try to use them
CIRCUITPYTHON_MODULES = [
    "board",
    "busio",
    "digitalio",
    "framebufferio",
    "rgbmatrix",
    "adafruit_matrixportal",
    "adafruit_matrixportal.matrixportal",
    "adafruit_matrixportal.graphics",
    "adafruit_matrixportal.matrix",
    "adafruit_matrixportal.network",
]

# Create basic mock modules
for module_name in CIRCUITPYTHON_MODULES:
    sys.modules[module_name] = MagicMock()

# Set up specific mocks with fake implementations for modules that need behavior
sys.modules["displayio"] = MagicMock(Group=FakeGroup)
sys.modules["terminalio"] = MagicMock(FONT=FakeTerminalio.FONT)
sys.modules["adafruit_display_text"] = MagicMock()
sys.modules["adafruit_display_text.label"] = MagicMock(Label=FakeLabel)

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
