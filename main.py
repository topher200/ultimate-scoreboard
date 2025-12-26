import asyncio

import board
from adafruit_matrixportal.matrixportal import MatrixPortal

from src.app_setup import (
    create_button_callbacks,
    create_managers,
    create_timing_indicator_task,
    initialize_application,
)
from src.hardware_manager import create_keys_from_board
from src.network_patches import apply_network_patches


async def main():
    """Main application entry point with asyncio tasks."""
    # Initialize hardware
    matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=True)

    # Apply network patches for faster failure behavior
    apply_network_patches(matrixportal)

    # Create keys from board
    keys = create_keys_from_board(board)

    # Initialize managers
    managers = create_managers(matrixportal, keys)

    # Initialize application state
    await initialize_application(managers.game_controller, managers.network_manager)

    # Run all tasks concurrently
    await asyncio.gather(
        managers.hardware_manager.monitor_buttons(
            create_button_callbacks(managers.game_controller)
        ),
        create_timing_indicator_task(
            managers.timing_indicator_manager, managers.display_manager
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
