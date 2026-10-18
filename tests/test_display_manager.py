"""Basic tests for display_manager using fake implementations."""

from src.display_manager import (
    CONNECTING,
    FONT_HEIGHT,
    GENDER_MATCHUP,
    GENDER_MATCHUP_COUNTER,
    GENDER_MATCHUP_COUNTER_Y_OFFSET,
    GENDER_MATCHUP_Y_POSITION,
    LEFT_TEAM,
    LEFT_TEAM_SCORE,
    MMP_GENDER_MATCHUP_COLOR,
    RIGHT_TEAM,
    RIGHT_TEAM_SCORE,
    TIMING_INDICATOR_Y_POSITION,
    WMP_GENDER_MATCHUP_COLOR,
    WMP_GENDER_MATCHUP_TEXT_COLOR,
)
from src.gender_manager import GenderManager


def _root_group(fake_matrix_portal):
    return fake_matrix_portal.display.root_group


class TestDisplayManager:
    """Test DisplayManager with fake hardware."""

    def test_root_group_holds_labels_and_timing_indicator(
        self, display_manager, fake_matrix_portal
    ):
        """Test that the root group holds 7 labels plus the timing indicator."""
        assert len(_root_group(fake_matrix_portal)) == 8

    def test_set_team_names(self, display_manager):
        display_manager.set_team_names("Red Team", "Blue Team")
        assert display_manager._labels[LEFT_TEAM].text == "Red Team"
        assert display_manager._labels[RIGHT_TEAM].text == "Blue Team"

    def test_set_scores(self, display_manager):
        display_manager.set_scores(42, 3)
        assert display_manager._labels[LEFT_TEAM_SCORE].text == "42"
        assert display_manager._labels[RIGHT_TEAM_SCORE].text == "3"

    def test_set_gender_matchup_wmp(self, display_manager):
        display_manager.set_gender_matchup(GenderManager.GENDER_WMP, 2)
        matchup = display_manager._labels[GENDER_MATCHUP]
        counter = display_manager._labels[GENDER_MATCHUP_COUNTER]
        assert (matchup.text, counter.text) == ("WMP", "2")
        assert matchup.color == counter.color == WMP_GENDER_MATCHUP_TEXT_COLOR
        assert matchup.background_color == WMP_GENDER_MATCHUP_COLOR
        assert counter.background_color is None

    def test_set_gender_matchup_mmp(self, display_manager):
        display_manager.set_gender_matchup(GenderManager.GENDER_MMP, 1)
        matchup = display_manager._labels[GENDER_MATCHUP]
        counter = display_manager._labels[GENDER_MATCHUP_COUNTER]
        assert (matchup.text, counter.text) == ("MMP", "1")
        assert matchup.color == counter.color == MMP_GENDER_MATCHUP_COLOR
        assert matchup.background_color is None

    def test_set_gender_matchup_mmp_clears_wmp_background(self, display_manager):
        display_manager.set_gender_matchup(GenderManager.GENDER_WMP, 1)
        display_manager.set_gender_matchup(GenderManager.GENDER_MMP, 1)
        assert display_manager._labels[GENDER_MATCHUP].background_color is None

    def test_wmp_background_ends_above_timing_indicator(self, display_manager):
        matchup = display_manager._labels[GENDER_MATCHUP]
        background_bottom = (
            GENDER_MATCHUP_Y_POSITION + FONT_HEIGHT + matchup.padding_bottom - 1
        )
        counter_top = GENDER_MATCHUP_Y_POSITION + GENDER_MATCHUP_COUNTER_Y_OFFSET
        assert counter_top + FONT_HEIGHT - 1 > background_bottom >= counter_top
        assert background_bottom < TIMING_INDICATOR_Y_POSITION

    def test_show_connecting(self, display_manager):
        display_manager.show_connecting(True)
        assert display_manager._labels[CONNECTING].text == "."
        display_manager.show_connecting(False)
        assert display_manager._labels[CONNECTING].text == " "

    def test_timing_indicator_on_bottom_row(self, display_manager, fake_matrix_portal):
        """Test that the timing indicator sits on the bottom row, right-aligned."""
        from src.display_manager import (
            DISPLAY_HEIGHT,
            DISPLAY_WIDTH,
            LEFT_BORDER_MARGIN_WIDTH,
        )
        from src.timing_indicator import TIMING_INDICATOR_PIXEL_COUNT

        tile_grid = _root_group(fake_matrix_portal)[-1]
        assert tile_grid.y == DISPLAY_HEIGHT - 1
        assert tile_grid.x + TIMING_INDICATOR_PIXEL_COUNT == (
            DISPLAY_WIDTH - LEFT_BORDER_MARGIN_WIDTH
        )
        assert tile_grid.bitmap.width == TIMING_INDICATOR_PIXEL_COUNT

    def _lit_pixels(self, display_manager):
        bitmap = display_manager._timing_indicator_bitmap
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
