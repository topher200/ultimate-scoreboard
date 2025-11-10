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

    def test_gender_matchup_color_swapping(self, display_manager):
        """Test that color changes when swapping between MMP and WMP."""
        # Test WMP gets one color
        display_manager.set_text("gender_matchup", "WMP")
        matchup_label = display_manager.text_elements["gender_matchup"]["label"]
        wmp_color = matchup_label.color

        # Test MMP gets a different color
        display_manager.set_text("gender_matchup", "MMP")
        matchup_label = display_manager.text_elements["gender_matchup"]["label"]
        mmp_color = matchup_label.color
        assert wmp_color != mmp_color

        # Test counter also changes color correctly
        display_manager.set_text("gender_matchup_counter", "WMP")
        counter_label = display_manager.text_elements["gender_matchup_counter"][
            "label"
        ]
        counter_wmp_color = counter_label.color

        display_manager.set_text("gender_matchup_counter", "MMP")
        counter_label = display_manager.text_elements["gender_matchup_counter"][
            "label"
        ]
        counter_mmp_color = counter_label.color
        assert counter_wmp_color != counter_mmp_color

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

    def test_all_labels_in_group(self, display_manager):
        """Test that all labels are appended to the main group."""
        expected_label_count = 7  # 7 text elements
        assert len(display_manager.main_group) == expected_label_count
