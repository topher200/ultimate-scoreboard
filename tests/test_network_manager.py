"""Tests for NetworkManager using fake implementations."""

from unittest.mock import MagicMock

import pytest

from src.network_manager import NetworkManager


class TestNetworkManager:
    """Test NetworkManager with fake hardware."""

    def test_initialization(self, network_manager):
        """Test that NetworkManager initializes without errors."""
        assert network_manager is not None

    def test_feed_key_constants_defined(self):
        """Test that all feed key constants are defined."""
        assert NetworkManager.TEAM_LEFT_TEAM_FEED
        assert NetworkManager.TEAM_RIGHT_TEAM_FEED


class TestNetworkManagerTeamNames:
    @pytest.mark.asyncio
    async def test_get_left_team_name_with_valid_data(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting left team name with valid data."""
        fake_matrix_portal.set_feed_value(
            NetworkManager.TEAM_LEFT_TEAM_FEED, "Red Team"
        )

        result = await network_manager.get_left_team_name()

        assert result == "Red Team"

    @pytest.mark.asyncio
    async def test_get_right_team_name_with_valid_data(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting right team name with valid data."""
        fake_matrix_portal.set_feed_value(
            NetworkManager.TEAM_RIGHT_TEAM_FEED, "Blue Team"
        )

        result = await network_manager.get_right_team_name()

        assert result == "Blue Team"

    @pytest.mark.asyncio
    async def test_show_connecting_called_on_successful_fetch(
        self, network_manager, fake_matrix_portal
    ):
        """Test that show_connecting is called with True before fetch and False after."""
        fake_matrix_portal.set_feed_value(
            NetworkManager.TEAM_LEFT_TEAM_FEED, "Red Team"
        )
        mock_show_connecting = MagicMock()
        network_manager.display_manager.show_connecting = mock_show_connecting

        await network_manager.get_left_team_name()

        assert mock_show_connecting.call_count == 2
        mock_show_connecting.assert_any_call(True)
        mock_show_connecting.assert_any_call(False)

    @pytest.mark.asyncio
    async def test_show_connecting_called_on_exception(
        self, network_manager, fake_matrix_portal
    ):
        """Test that show_connecting(False) is called even when an exception occurs."""
        mock_show_connecting = MagicMock()
        network_manager.display_manager.show_connecting = mock_show_connecting
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, None)

        await network_manager.get_left_team_name()

        assert mock_show_connecting.call_count == 2
        mock_show_connecting.assert_any_call(True)
        mock_show_connecting.assert_any_call(False)
