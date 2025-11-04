import time

import board  # ty: ignore[unresolved-import]
import digitalio  # type: ignore[import-untyped]
from adafruit_matrixportal.matrixportal import MatrixPortal
from display_manager import DisplayManager
from network_manager import NetworkManager
from score_manager import ScoreManager

# --- Display setup ---
matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,  # ty: ignore[possibly-missing-attribute]
    debug=False,
)
text_manager = DisplayManager(matrixportal)
network_manager = NetworkManager(matrixportal)

NETWORK_REFRESH_DELAY = 4  # seconds
"""The delay between requests to refresh data from the network."""

score_manager = ScoreManager(network_manager)

# --- Button setup ---
button_up = digitalio.DigitalInOut(board.BUTTON_UP)  # type: ignore[attr-defined]
button_up.direction = digitalio.Direction.INPUT
button_up.pull = digitalio.Pull.UP
button_up_pressed = False

button_down = digitalio.DigitalInOut(board.BUTTON_DOWN)  # type: ignore[attr-defined]
button_down.direction = digitalio.Direction.INPUT
button_down.pull = digitalio.Pull.UP
button_down_pressed = False


def show_connecting(show):
    text_manager.show_connecting(show)


def update_teams_and_gender_matchup():
    team_left_team = "Red"
    team_right_team = "Blue"
    gender_matchup = "WMP"
    gender_matchup_count = 1

    team_name = network_manager.get_left_team_name()
    if team_name is not None:
        print(f"Team {team_left_team} is now Team {team_name}")
        team_left_team = team_name
    team_name = network_manager.get_right_team_name()
    if team_name is not None:
        print(f"Team {team_right_team} is now Team {team_name}")
        team_right_team = team_name
    text_manager.set_text("left_team", team_left_team)
    text_manager.set_text("right_team", team_right_team)
    text_manager.set_text("gender_matchup", gender_matchup)
    text_manager.set_text("gender_matchup_counter", str(gender_matchup_count))


def update_scores():
    print("Updating data from Adafruit IO")
    show_connecting(True)

    if score_manager.update_scores():
        update_teams_and_gender_matchup()

    text_manager.set_text("left_team_score", score_manager.left_score)
    text_manager.set_text("right_team_score", score_manager.right_score)
    show_connecting(False)


show_connecting(True)
update_teams_and_gender_matchup()
update_scores()
show_connecting(False)
last_update = time.monotonic()

while True:
    current_time = time.monotonic()

    # Check for UP button press (increment left score)
    if not button_up.value and not button_up_pressed:
        button_up_pressed = True
        print("UP button pressed! Incrementing left score...")
        show_connecting(True)
        if score_manager.increment_left_score():
            text_manager.set_text("left_team_score", score_manager.left_score)
            print(f"Left score updated: {score_manager.left_score}")
        show_connecting(False)
    elif button_up.value:
        button_up_pressed = False

    # Check for DOWN button press (increment right score)
    if not button_down.value and not button_down_pressed:
        button_down_pressed = True
        print("DOWN button pressed! Incrementing right score...")
        show_connecting(True)
        if score_manager.increment_right_score():
            text_manager.set_text("right_team_score", score_manager.right_score)
            print(f"Right score updated: {score_manager.right_score}")
        show_connecting(False)
    elif button_down.value:
        button_down_pressed = False

    if current_time > last_update + NETWORK_REFRESH_DELAY:
        update_scores()
        last_update = time.monotonic()

    # Sleep for a short time to check button frequently
    time.sleep(0.1)
