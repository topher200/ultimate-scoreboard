"""Pytest configuration and fixtures for mocking CircuitPython modules."""

import asyncio
import sys
from unittest.mock import MagicMock

import pytest

from fakes import (
    FakeButton,
    FakeGroup,
    FakeKeys,
    FakeLabel,
    FakeMatrixPortal,
    FakeTerminalio,
)
from fakes.fake_nvm import create_fake_nvm
from src.display_manager import (
    TIMING_INDICATOR_MAX_DOTS_TO_SHOW,
    TIMING_INDICATOR_REMOVAL_INTERVAL,
    DisplayManager,
)
from src.game_controller import GameController
from src.gender_manager import GenderManager
from src.hardware_manager import HardwareManager
from src.network_manager import NetworkManager
from src.nvm_storage import NvmStorage
from src.score_manager import ScoreManager
from src.timing_indicator import TimingIndicatorManager

# Mock CircuitPython-specific modules that don't exist in regular Python
# These must be mocked before any imports try to use them
_BASIC_MOCK_MODULES = [
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
for module_name in _BASIC_MOCK_MODULES:
    sys.modules[module_name] = MagicMock()

# Set up specific mocks with fake implementations
sys.modules["displayio"] = MagicMock(Group=FakeGroup)
sys.modules["keypad"] = MagicMock(Keys=FakeKeys)
sys.modules["terminalio"] = MagicMock(FONT=FakeTerminalio.FONT)

# Set up adafruit_display_text module hierarchy
label_module = MagicMock(Label=FakeLabel)
sys.modules["adafruit_display_text"] = MagicMock(label=label_module)
sys.modules["adafruit_display_text.label"] = label_module

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


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
        max_dots=TIMING_INDICATOR_MAX_DOTS_TO_SHOW,
        removal_interval=TIMING_INDICATOR_REMOVAL_INTERVAL,
    )


@pytest.fixture
def game_controller(
    score_manager, display_manager, network_manager, gender_manager, timing_indicator_manager
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
def nvm_storage():
    """Create NvmStorage backed by a fake NVM bytearray."""
    return NvmStorage(create_fake_nvm())


@pytest.fixture
def nvm_score_manager(nvm_storage):
    """Create ScoreManager instance backed by NVM storage."""
    return ScoreManager(nvm_storage=nvm_storage)


@pytest.fixture
def nvm_game_controller(
    nvm_score_manager, display_manager, network_manager, gender_manager, timing_indicator_manager
):
    """Create GameController instance with NVM-backed score manager."""
    return GameController(
        nvm_score_manager,
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
    mock_board.BUTTON_UP = MagicMock()
    mock_board.BUTTON_DOWN = MagicMock()
    mock_board.A1 = MagicMock()
    mock_board.A3 = MagicMock()

    return FakeKeys(
        (mock_board.BUTTON_UP, mock_board.BUTTON_DOWN, mock_board.A1, mock_board.A3),
        value_when_pressed=False,
        pull=True,
    )


@pytest.fixture
def hardware_manager(fake_keys):
    """Create HardwareManager instance with fake keys."""
    return HardwareManager(fake_keys)
