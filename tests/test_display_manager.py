"""Basic tests for display_manager using fake implementations."""

import pytest


class TestDisplayManager:
    """Test DisplayManager with fake hardware."""

    def test_initialization(self, display_manager, fake_matrix_portal):
        """Test that DisplayManager initializes without errors."""
        assert display_manager is not None
        assert display_manager.matrixportal == fake_matrix_portal
        assert display_manager.display == fake_matrix_portal.display

    def test_root_group_set(self, display_manager, fake_matrix_portal):
        """Test that root_group is set on display."""
        assert fake_matrix_portal.display.root_group is not None
        assert fake_matrix_portal.display.root_group == display_manager.main_group

    def test_text_elements_created(self, display_manager):
        """Test that all expected text elements are created."""
        expected_elements = [
            "left_team",
            "right_team",
            "left_team_score",
            "right_team_score",
            "gender_matchup",
            "gender_matchup_counter",
            "connecting",
        ]
        for element_id in expected_elements:
            assert element_id in display_manager.text_elements
            assert "label" in display_manager.text_elements[element_id]

    def test_set_text_left_team(self, display_manager):
        """Test setting text for left team."""
        display_manager.set_text("left_team", "Red Team")
        label = display_manager.text_elements["left_team"]["label"]
        assert label.text == "Red Team"

    def test_set_text_right_team(self, display_manager):
        """Test setting text for right team."""
        display_manager.set_text("right_team", "Blue Team")
        label = display_manager.text_elements["right_team"]["label"]
        assert label.text == "Blue Team"

    def test_set_text_left_score(self, display_manager):
        """Test setting text for left team score."""
        display_manager.set_text("left_team_score", "5")
        left_label = display_manager.text_elements["left_team_score"]["label"]
        assert left_label.text == "5"

    def test_set_text_right_score(self, display_manager):
        """Test setting text for right team score."""
        display_manager.set_text("right_team_score", "3")
        right_label = display_manager.text_elements["right_team_score"]["label"]
        assert right_label.text == "3"

    def test_set_text_gender_matchup(self, display_manager):
        """Test setting gender matchup text."""
        display_manager.set_text("gender_matchup", "WMP")
        label = display_manager.text_elements["gender_matchup"]["label"]
        assert label.text == "WMP"

    def test_set_text_invalid_element(self, display_manager):
        """Test that setting text for invalid element raises error."""
        with pytest.raises(ValueError) as excinfo:
            display_manager.set_text("invalid_element", "test")
        assert "Unknown text element" in str(excinfo.value)

    def test_show_connecting_true(self, display_manager):
        """Test showing connecting indicator."""
        display_manager.show_connecting(True)
        label = display_manager.text_elements["connecting"]["label"]
        assert label.text == "."

    def test_show_connecting_false(self, display_manager):
        """Test hiding connecting indicator."""
        display_manager.show_connecting(False)
        label = display_manager.text_elements["connecting"]["label"]
        assert label.text == " "

    def test_set_text_converts_to_string(self, display_manager):
        """Test that set_text converts content to string."""
        display_manager.set_text("left_team_score", 42)
        label = display_manager.text_elements["left_team_score"]["label"]
        assert label.text == "42"
        assert isinstance(label.text, str)

    def test_all_elements_in_group(self, display_manager):
        """Test that all labels and the timing indicator are appended to the main group."""
        # 7 text elements + timing indicator tile grid
        assert len(display_manager.main_group) == 8

    def test_timing_indicator_on_bottom_row(self, display_manager):
        """Test that the timing indicator sits on the bottom row, right-aligned."""
        from src.display_manager import (
            DISPLAY_HEIGHT,
            DISPLAY_WIDTH,
            LEFT_BORDER_MARGIN_WIDTH,
        )
        from src.timing_indicator import TIMING_INDICATOR_PIXEL_COUNT

        tile_grid = display_manager.main_group[-1]
        assert tile_grid.y == DISPLAY_HEIGHT - 1
        assert tile_grid.x + TIMING_INDICATOR_PIXEL_COUNT == (
            DISPLAY_WIDTH - LEFT_BORDER_MARGIN_WIDTH
        )
        assert tile_grid.bitmap.width == TIMING_INDICATOR_PIXEL_COUNT

    def _lit_pixels(self, display_manager):
        bitmap = display_manager.timing_indicator_bitmap
        return [bitmap[i, 0] for i in range(bitmap.width)]

    def test_timing_indicator_starts_empty(self, display_manager):
        """Test that the timing indicator shows no pixels on startup."""
        assert sum(self._lit_pixels(display_manager)) == 0

    def test_update_timing_indicator_lights_right_most_pixels(self, display_manager):
        """Test that update_timing_indicator lights the right-most pixels."""
        from src.timing_indicator import TIMING_INDICATOR_PIXEL_COUNT

        display_manager.update_timing_indicator(3)
        expected = [0] * (TIMING_INDICATOR_PIXEL_COUNT - 3) + [1] * 3
        assert self._lit_pixels(display_manager) == expected

    def test_update_timing_indicator_hides_all(self, display_manager):
        """Test that update_timing_indicator hides all pixels when count is 0."""
        display_manager.update_timing_indicator(3)
        display_manager.update_timing_indicator(0)
        assert sum(self._lit_pixels(display_manager)) == 0

    def test_update_timing_indicator_shows_all(self, display_manager):
        """Test that update_timing_indicator lights all pixels when count is max."""
        from src.timing_indicator import TIMING_INDICATOR_PIXEL_COUNT

        display_manager.update_timing_indicator(TIMING_INDICATOR_PIXEL_COUNT)
        assert self._lit_pixels(display_manager) == [1] * TIMING_INDICATOR_PIXEL_COUNT

    def test_update_timing_indicator_clamps_to_max(self, display_manager):
        """Test that update_timing_indicator clamps count to max."""
        from src.timing_indicator import TIMING_INDICATOR_PIXEL_COUNT

        display_manager.update_timing_indicator(TIMING_INDICATOR_PIXEL_COUNT + 10)
        assert self._lit_pixels(display_manager) == [1] * TIMING_INDICATOR_PIXEL_COUNT

    def test_update_timing_indicator_clamps_to_zero(self, display_manager):
        """Test that update_timing_indicator clamps negative count to 0."""
        display_manager.update_timing_indicator(-5)
        assert sum(self._lit_pixels(display_manager)) == 0
