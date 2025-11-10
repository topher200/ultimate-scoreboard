import asyncio

import board
from adafruit_matrixportal.matrixportal import MatrixPortal

from src.display_manager import DisplayManager
from src.game_controller import GameController
from src.gender_manager import GenderManager
from src.hardware_manager import (
    BUTTON_DOWN,
    BUTTON_UP,
    HardwareManager,
    create_keys_from_board,
)
from src.network_manager import NetworkManager
from src.network_patches import apply_network_patches
from src.score_manager import ScoreManager


async def sync_pending_changes(
    score_manager: ScoreManager, gender_manager: GenderManager
):
    """Periodically attempt to sync pending changes.

    Syncs both scores and gender when they have pending changes.
    """
    while True:
        if score_manager.has_pending_changes():
            await score_manager.try_sync_scores()

        if gender_manager.has_pending_changes():
            await gender_manager.try_sync_gender()

        # Use minimum delay between managers
        delay = min(
            score_manager.get_next_retry_delay(),
            gender_manager.get_next_retry_delay(),
        )
        await asyncio.sleep(delay)


async def fetch_network_updates(game_controller: GameController):
    """Periodically fetch updates from the network with exponential backoff."""
    while True:
        await game_controller.update_from_network()
        await asyncio.sleep(game_controller.get_next_update_delay())


async def initial_network_fetch(game_controller: GameController):
    """One-time attempt to fetch initial values from network.

    Wraps network calls in try/except to handle network unavailability gracefully.
    Runs once and exits, allowing the system to start with defaults.
    """
    try:
        await game_controller.update_from_network()
        await game_controller.update_team_names_and_gender()
    except Exception as e:
        print(f"Initial network fetch failed: {e}")


async def main():
    """Main application entry point with asyncio tasks."""
    # Initialize hardware
    matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

    # Apply network patches for faster failure behavior
    apply_network_patches(matrixportal)

    # Initialize managers
    display_manager = DisplayManager(matrixportal)
    network_manager = NetworkManager(matrixportal, display_manager)
    score_manager = ScoreManager(network_manager)
    gender_manager = GenderManager(network_manager)
    keys = create_keys_from_board(board)
    hardware_manager = HardwareManager(keys=keys)
    game_controller = GameController(
        score_manager, display_manager, network_manager, gender_manager
    )

    # Initial setup
    try:
        await game_controller.update_team_names_and_gender()
    except Exception as e:
        # If network fails during initialization, set defaults manually
        print(f"Network unavailable during initialization: {e}")
        display_manager.set_text("left_team", NetworkManager.DEFAULT_LEFT_TEAM_NAME)
        display_manager.set_text("right_team", NetworkManager.DEFAULT_RIGHT_TEAM_NAME)
    # Always set scores and gender matchup
    display_manager.set_text("left_team_score", score_manager.left_score)
    display_manager.set_text("right_team_score", score_manager.right_score)
    game_controller._update_gender_matchup_display()

    # Run all tasks concurrently
    await asyncio.gather(
        hardware_manager.monitor_buttons(
            {
                BUTTON_UP: game_controller.handle_toggle_gender_button,
                BUTTON_DOWN: game_controller.handle_left_score_button,
            }
        ),
        sync_pending_changes(score_manager, gender_manager),
        fetch_network_updates(game_controller),
        initial_network_fetch(game_controller),
    )


if __name__ == "__main__":
    asyncio.run(main())
