"""Pixel tests for the DisplayManager layout, rendered with the real terminalio font."""

from tests.test_display_renderer import _run


def test_gender_matchup_clears_two_digit_scores():
    """Test that a dark column separates the matchup text from every two-digit score."""
    gaps = _run(
        """
import json
from simulator.display_renderer import render_pixels
from simulator.simulator_matrixportal import SimulatorMatrixPortal
from src.display_manager import (
    DisplayManager, GENDER_MATCHUP, LEFT_TEAM_SCORE, RIGHT_TEAM_SCORE,
)

matrixportal = SimulatorMatrixPortal()
display_manager = DisplayManager(matrixportal)
root = matrixportal.display.root_group
labels = display_manager._labels

def ink_columns(element_id):
    for item in root:
        item.hidden = item is not labels[element_id]
    pixels = render_pixels(root)
    return {i % 64 for i, color in enumerate(pixels) if color}

gaps = []
for gender in ("WMP", "MMP"):
    display_manager.set_gender_matchup(gender, 1)
    matchup = ink_columns(GENDER_MATCHUP)
    for score in range(10, 20):
        display_manager.set_scores(score, score)
        left = ink_columns(LEFT_TEAM_SCORE)
        right = ink_columns(RIGHT_TEAM_SCORE)
        gaps.append(min(matchup) - max(left) - 1)
        gaps.append(min(right) - max(matchup) - 1)
print(json.dumps(gaps))
"""
    )
    assert min(gaps) >= 1


def test_wifi_search_fits_the_screen():
    """Test that the Wi-Fi icon and "Searching" stay on screen and apart."""
    bounds = _run(
        """
import json
from simulator.display_renderer import render_pixels
from simulator.simulator_matrixportal import SimulatorMatrixPortal
from src.display_manager import DisplayManager

matrixportal = SimulatorMatrixPortal()
display_manager = DisplayManager(matrixportal)
search = display_manager._wifi_search
background, icon, text = search[0], search[1], search[2]
root = matrixportal.display.root_group

def ink(layer):
    for item in root:
        item.hidden = item is not search
    for item in search:
        item.hidden = item is not layer
    lit = [i for i, color in enumerate(render_pixels(root)) if color]
    columns = [i % 64 for i in lit]
    rows = [i // 64 for i in lit]
    return [min(columns), max(columns), min(rows), max(rows)]

print(json.dumps({"icon": ink(icon), "text": ink(text)}))
"""
    )
    icon_left, icon_right, icon_top, icon_bottom = bounds["icon"]
    text_left, text_right, text_top, text_bottom = bounds["text"]
    assert icon_top > 0
    assert text_left > 0 and text_right < 63
    assert text_bottom < 31
    assert icon_bottom < text_top
