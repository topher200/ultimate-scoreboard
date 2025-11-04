"""Tests for NetworkManager using fake implementations."""

import pytest
from network_manager import NetworkManager

from fakes import FakeMatrixPortal


class TestNetworkManager:
    """Test NetworkManager with fake hardware."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.fake_portal = FakeMatrixPortal()
        self.network_manager = NetworkManager(self.fake_portal)

    def test_initialization(self):
        """Test that NetworkManager initializes without errors."""
        assert self.network_manager is not None

    def test_feed_key_constants_defined(self):
        """Test that all feed key constants are defined."""
        assert NetworkManager.SCORES_LEFT_TEAM_FEED
        assert NetworkManager.SCORES_RIGHT_TEAM_FEED
        assert NetworkManager.TEAM_LEFT_TEAM_FEED
        assert NetworkManager.TEAM_RIGHT_TEAM_FEED

    def test_get_left_team_score_with_valid_data(self):
        """Test getting left team score with valid data."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)

        result = self.network_manager.get_left_team_score()

        assert result == 5

    def test_get_right_team_score_with_valid_data(self):
        """Test getting right team score with valid data."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        result = self.network_manager.get_right_team_score()

        assert result == 3

    def test_get_left_team_name_with_valid_data(self):
        """Test getting left team name with valid data."""
        self.fake_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Red Team")

        result = self.network_manager.get_left_team_name()

        assert result == "Red Team"

    def test_get_right_team_name_with_valid_data(self):
        """Test getting right team name with valid data."""
        self.fake_portal.set_feed_value(
            NetworkManager.TEAM_RIGHT_TEAM_FEED, "Blue Team"
        )

        result = self.network_manager.get_right_team_name()

        assert result == "Blue Team"

    def test_get_left_team_score_with_none_value(self):
        """Test getting left team score when feed returns None."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, None)

        result = self.network_manager.get_left_team_score()

        assert result is None

    def test_get_right_team_score_with_missing_feed(self):
        """Test getting right team score for a feed that doesn't exist."""
        result = self.network_manager.get_right_team_score()

        assert result is None

    def test_get_left_team_score_with_string_number(self):
        """Test getting left team score with string number data."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, "15")

        result = self.network_manager.get_left_team_score()

        assert result == "15"
