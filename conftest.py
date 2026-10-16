"""Pytest configuration and fixtures for mocking CircuitPython modules."""

import sys
from unittest.mock import MagicMock

import pytest

from fakes import (
    FakeBitmap,
    FakeGroup,
    FakeKeys,
    FakeLabel,
    FakeMatrixPortal,
    FakePalette,
    FakeTerminalio,
    FakeTileGrid,
)

# Mock CircuitPython-specific modules that don't exist in regular Python
_BASIC_MOCK_MODULES = [
    "board",
    "busio",
    "framebufferio",
    "rgbmatrix",
    "adafruit_matrixportal",
    "adafruit_matrixportal.matrixportal",
    "adafruit_matrixportal.graphics",
    "adafruit_matrixportal.matrix",
    "adafruit_matrixportal.network",
]

# Create basic mock modules
for module_name in _BASIC_MOCK_MODULES:
    sys.modules[module_name] = MagicMock()

# Set up specific mocks with fake implementations
sys.modules["displayio"] = MagicMock(
    Group=FakeGroup, Bitmap=FakeBitmap, Palette=FakePalette, TileGrid=FakeTileGrid
)
sys.modules["keypad"] = MagicMock(Keys=FakeKeys)
sys.modules["terminalio"] = MagicMock(FONT=FakeTerminalio.FONT)

# Set up adafruit_display_text module hierarchy
label_module = MagicMock(Label=FakeLabel)
sys.modules["adafruit_display_text"] = MagicMock(label=label_module)
sys.modules["adafruit_display_text.label"] = label_module

# src imports these modules, so it must load after the fakes above
from src.display_manager import DisplayManager
from src.game_controller import GameController
from src.gender_manager import GenderManager
from src.hardware_manager import HardwareManager
from src.network_manager import NetworkManager
from src.score_manager import ScoreManager
from src.timing_indicator import (
    TIMING_INDICATOR_PIXEL_COUNT,
    TIMING_INDICATOR_REMOVAL_INTERVAL,
    TimingIndicatorManager,
)


@pytest.fixture
def fake_matrix_portal():
    """Create FakeMatrixPortal instance for testing."""
    return FakeMatrixPortal()


@pytest.fixture
def network_manager(fake_matrix_portal, display_manager):
    """Create NetworkManager instance with fake hardware."""
    return NetworkManager(fake_matrix_portal, display_manager)


@pytest.fixture
def display_manager(fake_matrix_portal):
    """Create DisplayManager instance with fake hardware."""
    return DisplayManager(fake_matrix_portal)


@pytest.fixture
def score_manager():
    """Create ScoreManager instance."""
    return ScoreManager()


@pytest.fixture
def gender_manager():
    """Create GenderManager instance."""
    return GenderManager()


@pytest.fixture
def timing_indicator_manager():
    """Create TimingIndicatorManager instance."""
    return TimingIndicatorManager(
        max_dots=TIMING_INDICATOR_PIXEL_COUNT,
        removal_interval=TIMING_INDICATOR_REMOVAL_INTERVAL,
    )


@pytest.fixture
def game_controller(
    score_manager,
    display_manager,
    network_manager,
    gender_manager,
    timing_indicator_manager,
):
    """Create GameController instance with all managers."""
    return GameController(
        score_manager,
        display_manager,
        network_manager,
        gender_manager,
        timing_indicator_manager,
    )


@pytest.fixture
def fake_keys():
    """Create fake Keys object for hardware tests."""
    # Create a mock board-like object with pin attributes
    mock_board = MagicMock()

    return FakeKeys(
        (mock_board.A1, mock_board.A3),
        value_when_pressed=False,
        pull=True,
    )


@pytest.fixture
def hardware_manager(fake_keys):
    """Create HardwareManager instance with fake keys."""
    return HardwareManager(fake_keys)
