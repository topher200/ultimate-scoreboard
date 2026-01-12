"""Local development entry point with visual display simulator."""

import asyncio

from fakes.fake_keypad import FakeKeys
from simulator.display_window import DisplayWindow
from simulator.simulator_matrixportal import SimulatorMatrixPortal
from src.app_setup import (
    create_button_callbacks,
    create_managers,
    create_simultaneous_callbacks,
    create_timing_indicator_task,
    initialize_application,
)


async def local_main():
    """Main application entry point for local development with visual display."""
    # Initialize simulator hardware (visual display)
    matrixportal = SimulatorMatrixPortal()

    # Use test fakes for other hardware
    mock_board = type("Board", (), {})()
    mock_board.BUTTON_UP = object()
    mock_board.BUTTON_DOWN = object()
    mock_board.A1 = object()
    mock_board.A3 = object()

    keys = FakeKeys(
        (mock_board.BUTTON_UP, mock_board.BUTTON_DOWN, mock_board.A1, mock_board.A3),
        value_when_pressed=False,
        pull=True,
    )

    # Initialize managers using shared setup
    managers = create_managers(matrixportal, keys)

    # Initialize application state
    await initialize_application(managers.game_controller, managers.network_manager)

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

    # Run all tasks concurrently
    try:
        await asyncio.gather(
            managers.hardware_manager.monitor_buttons(
                create_button_callbacks(managers.game_controller),
                create_simultaneous_callbacks(managers.game_controller),
            ),
            create_timing_indicator_task(
                managers.timing_indicator_manager, managers.display_manager
            ),
            run_display_updates(),  # Simulator-specific
            return_exceptions=True,
        )
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nShutting down...")
    finally:
        display_window.stop()


if __name__ == "__main__":
    asyncio.run(local_main())

