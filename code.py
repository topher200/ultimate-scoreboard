import time

import board  # ty: ignore[unresolved-import]
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

UPDATE_DELAY = 4  # seconds

score_manager = ScoreManager(network_manager)


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

    if current_time > last_update + UPDATE_DELAY:
        update_scores()
        last_update = time.monotonic()
    time.sleep(max(0.1, UPDATE_DELAY - (current_time - last_update)))
