# Adapted from:
# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Scoreboard matrix display
# uses AdafruitIO to set scores and team names for a scoreboard
# Perfect for cornhole, ping pong, and other games

import time
import board
from adafruit_matrixportal.matrixportal import MatrixPortal

from text_manager import ScoreboardTextManager

# --- Display setup ---
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=False)
text_manager = ScoreboardTextManager(matrixportal)

SCORES_LEFT_TEAM_FEED = "scores-group.red-team-score-feed"
SCORES_RIGHT_TEAM_FEED = "scores-group.blue-team-score-feed"
TEAM_LEFT_TEAM_FEED = "scores-group.red-team-name"
TEAM_RIGHT_TEAM_FEED = "scores-group.blue-team-name"
UPDATE_DELAY = 4  # seconds

# Store the latest scores to detect changes
latest_left_team_score = None
latest_right_team_score = None


def show_connecting(show):
    text_manager.show_connecting(show)


def get_last_data(feed_key):
    feed = matrixportal.get_io_feed(feed_key, detailed=True)
    value = feed["details"]["data"]["last"]
    if value is not None:
        return value["value"]
    return None


def customize_team_names():
    team_left_team = "Red"
    team_right_team = "Blue"

    team_name = get_last_data(TEAM_LEFT_TEAM_FEED)
    if team_name is not None:
        print("Team {} is now Team {}".format(team_left_team, team_name))
        team_left_team = team_name
    team_name = get_last_data(TEAM_RIGHT_TEAM_FEED)
    if team_name is not None:
        print("Team {} is now Team {}".format(team_right_team, team_name))
        team_right_team = team_name
    text_manager.set_text("left_team", team_left_team)
    text_manager.set_text("right_team", team_right_team)


def update_scores():
    global latest_left_team_score, latest_right_team_score

    print("Updating data from Adafruit IO")
    show_connecting(True)

    score_left_team = get_last_data(SCORES_LEFT_TEAM_FEED)
    if score_left_team is None:
        score_left_team = 0
    score_right_team = get_last_data(SCORES_RIGHT_TEAM_FEED)
    if score_right_team is None:
        score_right_team = 0

    change_detected = False
    if latest_left_team_score is not None and score_left_team != latest_left_team_score:
        change_detected = True
    if (
        latest_right_team_score is not None
        and score_right_team != latest_right_team_score
    ):
        change_detected = True

    if change_detected:
        # use this as a chance to update team names
        customize_team_names()

    text_manager.set_text("left_team_score", score_left_team)
    text_manager.set_text("right_team_score", score_right_team)
    latest_left_team_score = score_left_team
    latest_right_team_score = score_right_team
    show_connecting(False)


show_connecting(True)
customize_team_names()
update_scores()
show_connecting(False)
last_update = time.monotonic()

while True:
    current_time = time.monotonic()
    if current_time > last_update + UPDATE_DELAY:
        update_scores()
        last_update = time.monotonic()
    time.sleep(min(0.1, max(0, last_update + UPDATE_DELAY)))
