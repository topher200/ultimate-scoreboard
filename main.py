import asyncio

import board
from adafruit_matrixportal.matrixportal import MatrixPortal

from src.display_manager import DisplayManager
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
    keys = create_keys_from_board(board)
    hardware_manager = HardwareManager(keys=keys)
    game_controller = GameController(
        score_manager, display_manager, network_manager, gender_manager
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
    )


if __name__ == "__main__":
    asyncio.run(main())
