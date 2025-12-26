import asyncio

import board
from adafruit_matrixportal.matrixportal import MatrixPortal

from src.display_manager import (
    TIMING_INDICATOR_MAX_DOTS_TO_SHOW,
    TIMING_INDICATOR_REMOVAL_INTERVAL,
    DisplayManager,
)
from src.game_controller import GameController
from src.gender_manager import GenderManager
from src.hardware_manager import (
    BUTTON_DOWN,
    BUTTON_LEFT,
    BUTTON_RIGHT,
    BUTTON_UP,
    HardwareManager,
    create_keys_from_board,
)
from src.network_manager import NetworkManager
from src.network_patches import apply_network_patches
from src.score_manager import ScoreManager
from src.timing_indicator import TimingIndicatorManager


async def main():
    """Main application entry point with asyncio tasks."""
    # Initialize hardware
    matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

    # Apply network patches for faster failure behavior
    apply_network_patches(matrixportal)

    # Initialize managers
    display_manager = DisplayManager(matrixportal)
    network_manager = NetworkManager(matrixportal, display_manager)
    score_manager = ScoreManager()
    gender_manager = GenderManager()
    timing_indicator_manager = TimingIndicatorManager(
        max_dots=TIMING_INDICATOR_MAX_DOTS_TO_SHOW,
        removal_interval=TIMING_INDICATOR_REMOVAL_INTERVAL,
    )
    keys = create_keys_from_board(board)
    hardware_manager = HardwareManager(keys=keys)
    game_controller = GameController(
        score_manager,
        display_manager,
        network_manager,
        gender_manager,
        timing_indicator_manager,
    )

    # Initial setup
    try:
        await game_controller.update_team_names()
    except Exception as e:
        # If network fails during initialization, set defaults manually
        print(f"Network unavailable during initialization: {e}")
        game_controller.set_team_names(
            NetworkManager.DEFAULT_LEFT_TEAM_NAME,
            NetworkManager.DEFAULT_RIGHT_TEAM_NAME,
        )
    game_controller.initialize_scores()

    async def run_timing_indicator():
        """Periodically remove dots from timing indicator."""
        while True:
            await asyncio.sleep(timing_indicator_manager.removal_interval)
            if timing_indicator_manager.has_dots():
                timing_indicator_manager.remove_dot()
                display_manager.update_timing_indicator(
                    timing_indicator_manager.get_dot_count()
                )

    # Run all tasks concurrently
    await asyncio.gather(
        hardware_manager.monitor_buttons(
            {
                BUTTON_UP: game_controller.handle_toggle_gender_button,
                BUTTON_DOWN: game_controller.handle_left_score_button,
                BUTTON_LEFT: game_controller.handle_left_score_button,
                BUTTON_RIGHT: game_controller.handle_right_score_button,
            }
        ),
        run_timing_indicator(),
    )


if __name__ == "__main__":
    asyncio.run(main())
