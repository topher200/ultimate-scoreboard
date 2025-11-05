import time

import board  # ty: ignore[unresolved-import]
import digitalio  # type: ignore[import-untyped]
from adafruit_matrixportal.matrixportal import MatrixPortal
from display_manager import DisplayManager
from game_controller import GameController
from hardware_manager import HardwareManager
from network_manager import NetworkManager
from score_manager import ScoreManager

NETWORK_REFRESH_DELAY = 4  # seconds


def main():
    """Main application entry point."""
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
    game_controller.update_team_names()
    game_controller.update_from_network()
    text_manager.show_connecting(False)
    last_update = time.monotonic()

    # Main loop
    while True:
        current_time = time.monotonic()

        # Update button states
        hardware_manager.update()

        # Check for button presses
        if hardware_manager.is_button_pressed("up"):
            game_controller.handle_left_score_button()

        if hardware_manager.is_button_pressed("down"):
            game_controller.handle_right_score_button()

        # Periodic network update
        if current_time > last_update + NETWORK_REFRESH_DELAY:
            game_controller.update_from_network()
            last_update = time.monotonic()

        # Sleep for responsive button checking
        time.sleep(0.1)


if __name__ == "__main__":
    main()
