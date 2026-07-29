"""Shared application setup functions for main.py and local_main.py."""

import asyncio

from src.compat import Callable, NamedTuple
from src.display_manager import TIMING_INDICATOR_REMOVAL_INTERVAL, DisplayManager
from src.game_controller import GameController
from src.gender_manager import GenderManager
from src.hardware_manager import (
    BUTTON_LEFT,
    BUTTON_RIGHT,
    HardwareManager,
)
from src.network_manager import NetworkManager
from src.score_manager import ScoreManager
from src.timing_indicator import TimingIndicatorManager


class Managers(NamedTuple):
    """Container for all application managers."""

    display_manager: DisplayManager
    network_manager: NetworkManager
    score_manager: ScoreManager
    gender_manager: GenderManager
    timing_indicator_manager: TimingIndicatorManager
    hardware_manager: HardwareManager
    game_controller: GameController


def create_managers(matrixportal, keys) -> Managers:
    """Initialize all application managers.

    :param matrixportal: MatrixPortal instance (real or simulator)
    :param keys: Keys instance (real or fake) for button input
    :return: Managers named tuple containing all initialized managers
    """
    display_manager = DisplayManager(matrixportal)
    network_manager = NetworkManager(matrixportal, display_manager)
    score_manager = ScoreManager()
    gender_manager = GenderManager()
    from src.display_manager import TIMING_INDICATOR_MAX_DOTS_TO_SHOW

    timing_indicator_manager = TimingIndicatorManager(
        max_dots=TIMING_INDICATOR_MAX_DOTS_TO_SHOW,
        removal_interval=TIMING_INDICATOR_REMOVAL_INTERVAL,
    )
    hardware_manager = HardwareManager(keys=keys)
    game_controller = GameController(
        score_manager,
        display_manager,
        network_manager,
        gender_manager,
        timing_indicator_manager,
    )

    return Managers(
        display_manager=display_manager,
        network_manager=network_manager,
        score_manager=score_manager,
        gender_manager=gender_manager,
        timing_indicator_manager=timing_indicator_manager,
        hardware_manager=hardware_manager,
        game_controller=game_controller,
    )


async def initialize_application(
    game_controller: GameController, network_manager: NetworkManager
) -> None:
    """Initialize application state (team names and scores).

    :param game_controller: GameController instance
    :param network_manager: NetworkManager instance
    """
    try:
        await game_controller.update_team_names()
    except Exception as e:
        print(f"Network unavailable during initialization: {e}")
        game_controller.set_team_names(
            network_manager.DEFAULT_LEFT_TEAM_NAME,
            network_manager.DEFAULT_RIGHT_TEAM_NAME,
        )
    game_controller.initialize_scores()


def create_button_callbacks(game_controller: GameController) -> dict[str, Callable]:
    """Create button callback mapping for hardware manager.

    Individual button callbacks fire on release if no chord was detected.

    :param game_controller: GameController instance
    :return: Dictionary mapping button names to callback functions
    """
    return {
        BUTTON_LEFT: game_controller.handle_left_score_button,
        BUTTON_RIGHT: game_controller.handle_right_score_button,
    }


def create_chord_callbacks(
    game_controller: GameController,
) -> dict[tuple[str, str], Callable]:
    """Create chord callback mapping for hardware manager.

    Chords fire when one button is held and the other is pressed:
    - Hold LEFT, press RIGHT → toggle gender matchup
    - Hold RIGHT, press LEFT → undo last point

    :param game_controller: GameController instance
    :return: Dictionary mapping (held_button, pressed_button) to callback functions
    """
    return {
        (BUTTON_LEFT, BUTTON_RIGHT): game_controller.handle_toggle_gender_button,
        (BUTTON_RIGHT, BUTTON_LEFT): game_controller.handle_undo_button,
    }


async def create_timing_indicator_task(
    timing_indicator_manager: TimingIndicatorManager, display_manager: DisplayManager
) -> None:
    """Create and run the timing indicator task.

    Periodically removes dots from timing indicator.

    :param timing_indicator_manager: TimingIndicatorManager instance
    :param display_manager: DisplayManager instance
    """
    POLLING_INTERVAL = 0.1
    while True:
        if timing_indicator_manager.has_dots():
            await asyncio.sleep(timing_indicator_manager.removal_interval)
            if timing_indicator_manager.has_dots():
                timing_indicator_manager.remove_dot()
                display_manager.update_timing_indicator(
                    timing_indicator_manager.get_dot_count()
                )
        else:
            await asyncio.sleep(POLLING_INTERVAL)
