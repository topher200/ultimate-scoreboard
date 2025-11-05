import asyncio

import board  # ty: ignore[unresolved-import]
import digitalio  # type: ignore[import-untyped]
from adafruit_matrixportal.matrixportal import MatrixPortal
from display_manager import DisplayManager
from game_controller import GameController
from hardware_manager import HardwareManager
from network_manager import NetworkManager
from score_manager import ScoreManager


async def monitor_buttons(
    hardware_manager: HardwareManager, game_controller: GameController
):
    """Monitor button presses and handle score updates."""
    while True:
        hardware_manager.update()

        if hardware_manager.is_button_pressed("up"):
            await game_controller.handle_left_score_button()

        if hardware_manager.is_button_pressed("down"):
            await game_controller.handle_right_score_button()

        await asyncio.sleep(0.1)


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
        status_neopixel=board.NEOPIXEL,  # ty: ignore[possibly-missing-attribute]
        debug=False,
    )

    # Set up buttons
    button_up = digitalio.DigitalInOut(board.BUTTON_UP)  # type: ignore[attr-defined]
    button_up.direction = digitalio.Direction.INPUT
    button_up.pull = digitalio.Pull.UP

    button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)  # type: ignore[attr-defined]
    button_down.direction = digitalio.Direction.INPUT
    button_down.pull = digitalio.Pull.UP

    # Initialize managers
    text_manager = DisplayManager(matrixportal)
    network_manager = NetworkManager(matrixportal)
    score_manager = ScoreManager(network_manager)
    hardware_manager = HardwareManager({"up": button_up, "down": button_down})
    game_controller = GameController(score_manager, text_manager, network_manager)

    # Initial setup
    text_manager.show_connecting(True)
    await game_controller.update_team_names()
    await asyncio.sleep(0)
    await game_controller.update_from_network()
    text_manager.show_connecting(False)

    # Run all tasks concurrently
    await asyncio.gather(
        monitor_buttons(hardware_manager, game_controller),
        sync_pending_changes(score_manager),
        fetch_network_updates(game_controller),
    )


if __name__ == "__main__":
    asyncio.run(main())
