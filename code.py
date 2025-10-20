# Adapted from:
# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# Scoreboard matrix display
# uses AdafruitIO to set scores and team names for a scoreboard
# Perfect for cornhole, ping pong, and other games

import time
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal

import text_spacing

# --- Display setup ---
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=False)
text_spacing.set(matrixportal)

# Static 'Connecting' Text
matrixportal.add_text(
    text_font=terminalio.FONT,
    text_position=(59, 0),
)

SCORES_RED_FEED = "scores-group.red-team-score-feed"
SCORES_BLUE_FEED = "scores-group.blue-team-score-feed"
TEAM_RED_FEED = "scores-group.red-team-name"
TEAM_BLUE_FEED = "scores-group.blue-team-name"
UPDATE_DELAY = 4

# Store the latest scores to detect changes
latest_red_score = None
latest_blue_score = None


def show_connecting(show):
    if show:
        matrixportal.set_text(".", 4)
    else:
        matrixportal.set_text(" ", 4)


def get_last_data(feed_key):
    feed = matrixportal.get_io_feed(feed_key, detailed=True)
    value = feed["details"]["data"]["last"]
    if value is not None:
        return value["value"]
    return None


def customize_team_names():
    team_red = "Red"
    team_blue = "Blue"

    show_connecting(True)
    team_name = get_last_data(TEAM_RED_FEED)
    if team_name is not None:
        print("Team {} is now Team {}".format(team_red, team_name))
        team_red = team_name
    matrixportal.set_text(team_red, 2)
    team_name = get_last_data(TEAM_BLUE_FEED)
    if team_name is not None:
        print("Team {} is now Team {}".format(team_blue, team_name))
        team_blue = team_name
    matrixportal.set_text(team_blue, 3)
    show_connecting(False)


def update_scores():
    global latest_red_score, latest_blue_score

    print("Updating data from Adafruit IO")
    show_connecting(True)

    score_red = get_last_data(SCORES_RED_FEED)
    if score_red is None:
        score_red = 0
    score_blue = get_last_data(SCORES_BLUE_FEED)
    if score_blue is None:
        score_blue = 0

    change_detected = False
    if latest_red_score is not None and score_red != latest_red_score:
        change_detected = True
    if latest_blue_score is not None and score_blue != latest_blue_score:
        change_detected = True

    if change_detected:
        # use this as a chance to update team names
        customize_team_names()

    matrixportal.set_text(score_red, 0)
    matrixportal.set_text(score_blue, 1)
    latest_red_score = score_red
    latest_blue_score = score_blue
    show_connecting(False)


customize_team_names()
update_scores()
last_update = time.monotonic()

while True:
    current_time = time.monotonic()
    if current_time > last_update + UPDATE_DELAY:
        update_scores()
        last_update = time.monotonic()
    time.sleep(min(0.1, max(0, last_update + UPDATE_DELAY)))
