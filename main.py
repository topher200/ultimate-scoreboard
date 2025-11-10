import asyncio

import board
from adafruit_matrixportal.matrixportal import MatrixPortal

from src.display_manager import DisplayManager
from src.game_controller import GameController
from src.hardware_manager import (
    BUTTON_DOWN,
    BUTTON_UP,
    HardwareManager,
    create_buttons_from_board,
)
from src.network_manager import NetworkManager
from src.score_manager import ScoreManager


async def sync_pending_changes(score_manager: ScoreManager):
    """Periodically attempt to sync pending changes with exponential backoff."""
    while True:
        if score_manager.has_pending_changes():
            await score_manager.try_sync_scores()

        await asyncio.sleep(score_manager.get_next_retry_delay())


async def fetch_network_updates(game_controller: GameController):
    """Periodically fetch updates from the network with exponential backoff."""
    while True:
        await game_controller.update_from_network()
        await asyncio.sleep(game_controller.get_next_update_delay())


async def main():
    """Main application entry point with asyncio tasks."""
    # Initialize hardware
    matrixportal = MatrixPortal(
        status_neopixel=board.NEOPIXEL,
        debug=False,
    )

    # Initialize managers
    text_manager = DisplayManager(matrixportal)
    network_manager = NetworkManager(matrixportal)
    score_manager = ScoreManager(network_manager)
    buttons = create_buttons_from_board(board)
    hardware_manager = HardwareManager(buttons=buttons)
    game_controller = GameController(score_manager, text_manager, network_manager)

    # Initial setup
    text_manager.show_connecting(True)
    await game_controller.update_team_names()
    await asyncio.sleep(0)
    await game_controller.update_from_network()
    text_manager.show_connecting(False)

    # Run all tasks concurrently
    await asyncio.gather(
        hardware_manager.monitor_buttons(
            {
                BUTTON_UP: game_controller.handle_left_score_button,
                BUTTON_DOWN: game_controller.handle_right_score_button,
            }
        ),
        sync_pending_changes(score_manager),
        fetch_network_updates(game_controller),
    )


if __name__ == "__main__":
    asyncio.run(main())
