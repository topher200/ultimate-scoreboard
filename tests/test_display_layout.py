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
