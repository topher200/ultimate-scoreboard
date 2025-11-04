"""Tests for ScoreManager using fake implementations."""

import pytest
from network_manager import NetworkManager
from score_manager import ScoreManager

from fakes import FakeMatrixPortal


class TestScoreManager:
    """Test ScoreManager with fake hardware."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.fake_portal = FakeMatrixPortal()
        self.network_manager = NetworkManager(self.fake_portal)
        self.score_manager = ScoreManager(self.network_manager)

    def test_initialization(self):
        """Test that ScoreManager initializes without errors."""
        assert self.score_manager is not None
        assert self.score_manager.left_score is None
        assert self.score_manager.right_score is None

    def test_update_scores_with_none_values_defaults_to_zero(self):
        """Test that None feed values default to 0."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, None)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, None)

        changed = self.score_manager.update_scores()

        assert self.score_manager.left_score == 0
        assert self.score_manager.right_score == 0
        assert not changed

    def test_update_scores_with_initial_values(self):
        """Test updating scores with initial values."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        changed = self.score_manager.update_scores()

        assert self.score_manager.left_score == 5
        assert self.score_manager.right_score == 3
        assert not changed

    def test_update_scores_detects_left_score_change(self):
        """Test that update_scores returns True when left score changes."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        self.score_manager.update_scores()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)
        changed = self.score_manager.update_scores()

        assert self.score_manager.left_score == 6
        assert self.score_manager.right_score == 3
        assert changed

    def test_update_scores_detects_right_score_change(self):
        """Test that update_scores returns True when right score changes."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        self.score_manager.update_scores()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 4)
        changed = self.score_manager.update_scores()

        assert self.score_manager.left_score == 5
        assert self.score_manager.right_score == 4
        assert changed

    def test_update_scores_detects_both_scores_change(self):
        """Test that update_scores returns True when both scores change."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        self.score_manager.update_scores()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 4)
        changed = self.score_manager.update_scores()

        assert self.score_manager.left_score == 6
        assert self.score_manager.right_score == 4
        assert changed

    def test_update_scores_no_change_when_scores_same(self):
        """Test that update_scores returns False when scores don't change."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        self.score_manager.update_scores()

        changed = self.score_manager.update_scores()

        assert self.score_manager.left_score == 5
        assert self.score_manager.right_score == 3
        assert not changed

    def test_update_scores_with_string_values(self):
        """Test that update_scores handles string score values."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, "10")
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, "7")

        changed = self.score_manager.update_scores()

        assert self.score_manager.left_score == "10"
        assert self.score_manager.right_score == "7"
        assert not changed

    def test_update_scores_multiple_updates(self):
        """Test multiple score updates in sequence."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 0)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 0)
        self.score_manager.update_scores()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 1)
        changed1 = self.score_manager.update_scores()
        assert changed1

        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 1)
        changed2 = self.score_manager.update_scores()
        assert changed2

        changed3 = self.score_manager.update_scores()
        assert not changed3
