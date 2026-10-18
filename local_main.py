"""Local development entry point with visual display simulator."""

import asyncio
import sys

from fakes.fake_keypad import FakeKeys
from simulator.display_window import DisplayWindow
from simulator.simulator_matrixportal import SimulatorMatrixPortal
from simulator.simulator_web_server import SimulatorNetwork, SimulatorWebServer
from src.app_setup import create_managers, initialize_application, run_tasks
from src.lab import run_lab

SIMULATOR_NVM_SIZE = 8192


async def local_main():
    """Main application entry point for local development with visual display."""
    # Initialize simulator hardware (visual display)
    matrixportal = SimulatorMatrixPortal()

    # Use test fakes for other hardware
    mock_board = type("Board", (), {})()
    mock_board.A1 = object()
    mock_board.A3 = object()

    keys = FakeKeys(
        (mock_board.A1, mock_board.A3),
        value_when_pressed=False,
        pull=True,
    )

    nvm = bytearray(SIMULATOR_NVM_SIZE)
    lab_mode = "--lab" in sys.argv
    managers = None
    if not lab_mode:
        # Initialize managers using shared setup
        managers = create_managers(
            matrixportal, keys, nvm, SimulatorNetwork(), SimulatorWebServer()
        )
        # Initialize application state
        initialize_application(managers)

    # Initialize Pygame display window (simulator-specific)
    # Pass keys instance to enable keyboard button simulation
    display_window = DisplayWindow(matrixportal.display, scale=20, keys=keys)
    display_window.start()

    async def run_display_updates():
        """Periodically update the display window."""
        while display_window.is_running():
            display_window.update()
            await asyncio.sleep(1.0 / 30.0)
        # When window stops, cancel all other tasks
        tasks = asyncio.all_tasks()
        current_task = asyncio.current_task()
        for task in tasks:
            if task != current_task:
                task.cancel()

    try:
        if managers is None:
            await run_lab(
                matrixportal,
                keys,
                nvm,
                SimulatorNetwork(),
                SimulatorWebServer(),
                run_display_updates(),
            )
        else:
            await run_tasks(managers, run_display_updates())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nShutting down...")
    finally:
        display_window.stop()


if __name__ == "__main__":
    asyncio.run(local_main())
