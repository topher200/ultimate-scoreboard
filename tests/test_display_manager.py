"""Basic tests for display_manager using fake implementations."""

from src.display_manager import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    GENDER_MATCHUP,
    GENDER_MATCHUP_COUNTER,
    LEFT_TEAM,
    LEFT_TEAM_SCORE,
    MMP_GENDER_MATCHUP_COLOR,
    RIGHT_TEAM,
    RIGHT_TEAM_SCORE,
    WMP_GENDER_MATCHUP_COLOR,
)
from src.gender_manager import GenderManager


def _root_group(fake_matrix_portal):
    return fake_matrix_portal.display.root_group


class TestDisplayManager:
    """Test DisplayManager with fake hardware."""

    def test_root_group_holds_labels_and_timing_indicator(
        self, display_manager, fake_matrix_portal
    ):
        """Test that the root group holds labels, frames, timing indicator, and QR code."""
        assert len(_root_group(fake_matrix_portal)) == 11

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
        assert matchup.color == counter.color == WMP_GENDER_MATCHUP_COLOR
        assert not display_manager._wmp_frame.hidden
        assert display_manager._mmp_frame.hidden

    def test_set_gender_matchup_mmp(self, display_manager):
        display_manager.set_gender_matchup(GenderManager.GENDER_MMP, 1)
        matchup = display_manager._labels[GENDER_MATCHUP]
        counter = display_manager._labels[GENDER_MATCHUP_COUNTER]
        assert (matchup.text, counter.text) == ("MMP", "1")
        assert matchup.color == counter.color == MMP_GENDER_MATCHUP_COLOR
        assert display_manager._wmp_frame.hidden
        assert not display_manager._mmp_frame.hidden

    def test_frames_are_dashed_at_rest(self, display_manager):
        for frame in (display_manager._wmp_frame, display_manager._mmp_frame):
            top_row = [frame.bitmap[x, 0] for x in range(16)]
            assert top_row == [1, 1, 1, 1, 1, 0, 0, 0] * 2

    def test_mmp_frame_bottom_shows_only_when_timing_indicator_is_empty(
        self, display_manager
    ):
        bitmap = display_manager._mmp_frame.bitmap
        bottom_row = [bitmap[x, DISPLAY_HEIGHT - 1] for x in range(DISPLAY_WIDTH)]
        assert any(bottom_row)
        display_manager.update_timing_indicator(5)
        assert not any(bitmap[x, DISPLAY_HEIGHT - 1] for x in range(DISPLAY_WIDTH))
        display_manager.update_timing_indicator(0)
        assert [bitmap[x, DISPLAY_HEIGHT - 1] for x in range(DISPLAY_WIDTH)] == (
            bottom_row
        )

    def test_frames_light_only_the_screen_edge(self, display_manager):
        for frame in (display_manager._wmp_frame, display_manager._mmp_frame):
            for y in range(DISPLAY_HEIGHT):
                for x in range(DISPLAY_WIDTH):
                    on_edge = x in {0, DISPLAY_WIDTH - 1} or y in {
                        0,
                        DISPLAY_HEIGHT - 1,
                    }
                    if not on_edge:
                        assert frame.bitmap[x, y] == 0

    def test_show_and_hide_wifi_search(self, display_manager):
        assert not display_manager.wifi_search_shown

        display_manager.show_wifi_search()
        assert display_manager.wifi_search_shown

        display_manager.hide_wifi_search()
        assert not display_manager.wifi_search_shown

    def test_timing_indicator_above_bottom_row(
        self, display_manager, fake_matrix_portal
    ):
        """Test that the timing indicator sits above the bottom row, right-aligned."""
        from src.display_manager import LEFT_BORDER_MARGIN_WIDTH
        from src.timing_indicator import TIMING_INDICATOR_PIXEL_COUNT

        tile_grid = _root_group(fake_matrix_portal)[-3]
        assert tile_grid.y == DISPLAY_HEIGHT - 2
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
