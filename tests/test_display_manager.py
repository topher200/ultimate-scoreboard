"""Basic tests for display_manager using fake implementations."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from fakes import FakeGroup, FakeLabel, FakeMatrixPortal, FakeTerminalio


class TestDisplayManager:
    """Test DisplayManager with fake hardware."""

    @pytest.fixture(autouse=True)
    @patch.dict(
        sys.modules,
        {
            "terminalio": MagicMock(FONT=FakeTerminalio.FONT),
            "displayio": MagicMock(Group=FakeGroup),
            "adafruit_display_text": MagicMock(),
            "adafruit_display_text.label": MagicMock(Label=FakeLabel),
        },
    )
    def setup(self):
        """Set up test fixtures with mocked imports."""
        from display_manager import DisplayManager  # noqa: PLC0415

        self.DisplayManager = DisplayManager
        self.fake_portal = FakeMatrixPortal()
        self.text_manager = DisplayManager(self.fake_portal)

    def test_initialization(self):
        """Test that DisplayManager initializes without errors."""
        assert self.text_manager is not None
        assert self.text_manager.matrixportal == self.fake_portal
        assert self.text_manager.display == self.fake_portal.display

    def test_root_group_set(self):
        """Test that root_group is set on display."""
        assert self.fake_portal.display.root_group is not None
        assert self.fake_portal.display.root_group == self.text_manager.main_group

    def test_text_elements_created(self):
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
            assert element_id in self.text_manager.text_elements
            assert "label" in self.text_manager.text_elements[element_id]

    def test_set_text_left_team(self):
        """Test setting text for left team."""
        self.text_manager.set_text("left_team", "Red Team")
        label = self.text_manager.text_elements["left_team"]["label"]
        assert label.text == "Red Team"

    def test_set_text_right_team(self):
        """Test setting text for right team."""
        self.text_manager.set_text("right_team", "Blue Team")
        label = self.text_manager.text_elements["right_team"]["label"]
        assert label.text == "Blue Team"

    def test_set_text_left_score(self):
        """Test setting text for left team score."""
        self.text_manager.set_text("left_team_score", "5")
        left_label = self.text_manager.text_elements["left_team_score"]["label"]
        assert left_label.text == "5"

    def test_set_text_right_score(self):
        """Test setting text for right team score."""
        self.text_manager.set_text("right_team_score", "3")
        right_label = self.text_manager.text_elements["right_team_score"]["label"]
        assert right_label.text == "3"

    def test_set_text_gender_matchup(self):
        """Test setting gender matchup text."""
        self.text_manager.set_text("gender_matchup", "WMP")
        label = self.text_manager.text_elements["gender_matchup"]["label"]
        assert label.text == "WMP"

    def test_gender_matchup_color_swapping(self):
        """Test that color changes when swapping between MMP and WMP."""
        # Test WMP gets one color
        self.text_manager.set_text("gender_matchup", "WMP")
        matchup_label = self.text_manager.text_elements["gender_matchup"]["label"]
        wmp_color = matchup_label.color

        # Test MMP gets a different color
        self.text_manager.set_text("gender_matchup", "MMP")
        matchup_label = self.text_manager.text_elements["gender_matchup"]["label"]
        mmp_color = matchup_label.color
        assert wmp_color != mmp_color

        # Test counter also changes color correctly
        self.text_manager.set_text("gender_matchup_counter", "WMP")
        counter_label = self.text_manager.text_elements["gender_matchup_counter"][
            "label"
        ]
        counter_wmp_color = counter_label.color

        self.text_manager.set_text("gender_matchup_counter", "MMP")
        counter_label = self.text_manager.text_elements["gender_matchup_counter"][
            "label"
        ]
        counter_mmp_color = counter_label.color
        assert counter_wmp_color != counter_mmp_color

    def test_set_text_invalid_element(self):
        """Test that setting text for invalid element raises error."""
        with pytest.raises(ValueError) as excinfo:
            self.text_manager.set_text("invalid_element", "test")
        assert "Unknown text element" in str(excinfo.value)

    def test_show_connecting_true(self):
        """Test showing connecting indicator."""
        self.text_manager.show_connecting(True)
        label = self.text_manager.text_elements["connecting"]["label"]
        assert label.text == "."

    def test_show_connecting_false(self):
        """Test hiding connecting indicator."""
        self.text_manager.show_connecting(False)
        label = self.text_manager.text_elements["connecting"]["label"]
        assert label.text == " "

    def test_set_text_converts_to_string(self):
        """Test that set_text converts content to string."""
        self.text_manager.set_text("left_team_score", 42)
        label = self.text_manager.text_elements["left_team_score"]["label"]
        assert label.text == "42"
        assert isinstance(label.text, str)

    def test_all_labels_in_group(self):
        """Test that all labels are appended to the main group."""
        expected_label_count = 7  # 7 text elements
        assert len(self.text_manager.main_group) == expected_label_count
