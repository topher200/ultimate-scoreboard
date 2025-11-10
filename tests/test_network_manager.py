"""Tests for NetworkManager using fake implementations."""

import pytest

from src.network_manager import NetworkManager


class TestNetworkManager:
    """Test NetworkManager with fake hardware."""

    def test_initialization(self, network_manager):
        """Test that NetworkManager initializes without errors."""
        assert network_manager is not None

    def test_feed_key_constants_defined(self):
        """Test that all feed key constants are defined."""
        assert NetworkManager.SCORES_LEFT_TEAM_FEED
        assert NetworkManager.SCORES_RIGHT_TEAM_FEED
        assert NetworkManager.TEAM_LEFT_TEAM_FEED
        assert NetworkManager.TEAM_RIGHT_TEAM_FEED

    @pytest.mark.asyncio
    async def test_get_left_team_score_with_valid_data(self, network_manager, fake_matrix_portal):
        """Test getting left team score with valid data."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)

        result = await network_manager.get_left_team_score()

        assert result == 5

    @pytest.mark.asyncio
    async def test_get_right_team_score_with_valid_data(self, network_manager, fake_matrix_portal):
        """Test getting right team score with valid data."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        result = await network_manager.get_right_team_score()

        assert result == 3

    @pytest.mark.asyncio
    async def test_get_left_team_name_with_valid_data(self, network_manager, fake_matrix_portal):
        """Test getting left team name with valid data."""
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Red Team")

        result = await network_manager.get_left_team_name()

        assert result == "Red Team"

    @pytest.mark.asyncio
    async def test_get_right_team_name_with_valid_data(self, network_manager, fake_matrix_portal):
        """Test getting right team name with valid data."""
        fake_matrix_portal.set_feed_value(
            NetworkManager.TEAM_RIGHT_TEAM_FEED, "Blue Team"
        )

        result = await network_manager.get_right_team_name()

        assert result == "Blue Team"

    @pytest.mark.asyncio
    async def test_get_left_team_score_with_none_value(self, network_manager, fake_matrix_portal):
        """Test getting left team score when feed returns None."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, None)

        result = await network_manager.get_left_team_score()

        assert result == 0

    @pytest.mark.asyncio
    async def test_get_right_team_score_with_missing_feed(self, network_manager):
        """Test getting right team score for a feed that doesn't exist."""
        result = await network_manager.get_right_team_score()

        assert result == 0

    @pytest.mark.asyncio
    async def test_get_left_team_score_with_string_number(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting left team score with string number data."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, "15")

        result = await network_manager.get_left_team_score()

        assert result == 15
