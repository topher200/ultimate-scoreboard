import asyncio

import board
from adafruit_matrixportal.matrixportal import MatrixPortal

from src.app_setup import create_managers, initialize_application, run_tasks
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
    initialize_application(managers.game_controller)

    await run_tasks(managers)


if __name__ == "__main__":
    asyncio.run(main())
