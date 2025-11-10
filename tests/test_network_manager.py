"""Tests for NetworkManager using fake implementations."""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.gender_manager import GenderManager
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
        assert NetworkManager.FIRST_POINT_GENDER_FEED


class TestNetworkManagerScores:
    @pytest.mark.asyncio
    async def test_get_left_team_score_with_valid_data(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting left team score with valid data."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)

        result = await network_manager.get_left_team_score()

        assert result == 5

    @pytest.mark.asyncio
    async def test_get_right_team_score_with_valid_data(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting right team score with valid data."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        result = await network_manager.get_right_team_score()

        assert result == 3

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
    async def test_get_left_team_score_with_none_value(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting left team score when feed returns None."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, None)

        result = await network_manager.get_left_team_score()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_right_team_score_with_missing_feed(self, network_manager):
        """Test getting right team score for a feed that doesn't exist."""
        result = await network_manager.get_right_team_score()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_left_team_score_with_string_number(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting left team score with string number data."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, "15")

        result = await network_manager.get_left_team_score()

        assert result == 15

    @pytest.mark.asyncio
    async def test_show_connecting_called_on_successful_fetch(
        self, network_manager, fake_matrix_portal
    ):
        """Test that show_connecting is called with True before fetch and False after."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        mock_show_connecting = MagicMock()
        network_manager.display_manager.show_connecting = mock_show_connecting

        await network_manager.get_left_team_score()

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
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, None)

        await network_manager.get_left_team_score()

        assert mock_show_connecting.call_count == 2
        mock_show_connecting.assert_any_call(True)
        mock_show_connecting.assert_any_call(False)


class TestNetworkManagerGender:
    @pytest.mark.asyncio
    async def test_get_first_point_gender_with_mmp(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting first point gender with 'mmp' value."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "mmp")

        result = await network_manager.get_first_point_gender()

        assert result == GenderManager.GENDER_MMP

    @pytest.mark.asyncio
    async def test_get_first_point_gender_with_wmp(
        self, network_manager, fake_matrix_portal
    ):
        """Test getting first point gender with 'wmp' value."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "wmp")

        result = await network_manager.get_first_point_gender()

        assert result == GenderManager.GENDER_WMP

    @pytest.mark.asyncio
    async def test_get_first_point_gender_case_insensitive(
        self, network_manager, fake_matrix_portal
    ):
        """Test that gender feed value is case-insensitive."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "MMP")

        result = await network_manager.get_first_point_gender()

        assert result == GenderManager.GENDER_MMP

        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "WMP")

        result = await network_manager.get_first_point_gender()

        assert result == GenderManager.GENDER_WMP

    @pytest.mark.asyncio
    async def test_get_first_point_gender_defaults_to_wmp(
        self, network_manager, fake_matrix_portal
    ):
        """Test that get_first_point_gender defaults to 'wmp' when feed unavailable."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, None)

        result = await network_manager.get_first_point_gender()

        assert result == GenderManager.GENDER_WMP

    @pytest.mark.asyncio
    async def test_get_first_point_gender_invalid_value_defaults(
        self, network_manager, fake_matrix_portal
    ):
        """Test that invalid gender value defaults to 'wmp'."""
        fake_matrix_portal.set_feed_value(
            NetworkManager.FIRST_POINT_GENDER_FEED, "invalid"
        )

        result = await network_manager.get_first_point_gender()

        assert result == GenderManager.GENDER_WMP

    @pytest.mark.asyncio
    async def test_set_first_point_gender_with_mmp(
        self, network_manager, fake_matrix_portal
    ):
        """Test setting first point gender to 'mmp'."""
        await network_manager.set_first_point_gender(GenderManager.GENDER_MMP)

        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.FIRST_POINT_GENDER_FEED)
            == GenderManager.GENDER_MMP
        )

    @pytest.mark.asyncio
    async def test_set_first_point_gender_with_wmp(
        self, network_manager, fake_matrix_portal
    ):
        """Test setting first point gender to 'wmp'."""
        await network_manager.set_first_point_gender(GenderManager.GENDER_WMP)

        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.FIRST_POINT_GENDER_FEED)
            == GenderManager.GENDER_WMP
        )

    @pytest.mark.asyncio
    async def test_set_first_point_gender_case_insensitive(
        self, network_manager, fake_matrix_portal
    ):
        """Test that set_first_point_gender normalizes to lowercase."""
        await network_manager.set_first_point_gender("MMP")

        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.FIRST_POINT_GENDER_FEED)
            == GenderManager.GENDER_MMP
        )

    @pytest.mark.asyncio
    async def test_set_first_point_gender_invalid_value_raises(self, network_manager):
        """Test that setting invalid gender value raises ValueError."""
        with pytest.raises(ValueError, match="Invalid gender value"):
            await network_manager.set_first_point_gender("invalid")


class TestNetworkManagerCircuitBreaker:
    """Test circuit breaker functionality in NetworkManager."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_triggers_on_network_exception(
        self, network_manager, fake_matrix_portal
    ):
        """Test that circuit breaker triggers on network exception."""
        fake_matrix_portal.get_io_feed = MagicMock(
            side_effect=Exception("Network error")
        )

        result = await network_manager.get_left_team_score()

        assert result is None
        assert network_manager._circuit_breaker_open_until is not None

    @pytest.mark.asyncio
    async def test_circuit_breaker_skips_requests_when_open(
        self, network_manager, fake_matrix_portal
    ):
        """Test that requests are skipped when circuit breaker is open."""
        mock_get_io_feed = MagicMock(
            return_value={
                "details": {
                    "data": {
                        "last": {
                            "value": "5",
                        }
                    }
                }
            }
        )
        fake_matrix_portal.get_io_feed = mock_get_io_feed

        network_manager._circuit_breaker_open_until = time.monotonic() + 60

        result = await network_manager.get_left_team_score()

        assert result is None
        assert mock_get_io_feed.call_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_after_timeout(
        self, network_manager, fake_matrix_portal
    ):
        """Test that circuit breaker resets after 60 seconds."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        fake_matrix_portal.get_io_feed = MagicMock(
            side_effect=Exception("Network error")
        )

        await network_manager.get_left_team_score()

        assert network_manager._circuit_breaker_open_until is not None
        original_open_until = network_manager._circuit_breaker_open_until

        with patch("src.network_manager.time.monotonic") as mock_time:
            mock_time.return_value = original_open_until + 1
            mock_get_io_feed = MagicMock(
                return_value={
                    "details": {
                        "data": {
                            "last": {
                                "value": "5",
                            }
                        }
                    }
                }
            )
            fake_matrix_portal.get_io_feed = mock_get_io_feed

            result = await network_manager.get_left_team_score()

            assert result == 5
            assert mock_get_io_feed.call_count == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_applies_to_set_feed_value(
        self, network_manager, fake_matrix_portal
    ):
        """Test that circuit breaker applies to set_feed_value."""
        fake_matrix_portal.push_to_io = MagicMock(
            side_effect=Exception("Network error")
        )

        with pytest.raises(Exception, match="Network error"):
            await network_manager.set_left_team_score(5)

        assert network_manager._circuit_breaker_open_until is not None

        fake_matrix_portal.push_to_io = MagicMock()
        await network_manager.set_left_team_score(10)

        assert fake_matrix_portal.push_to_io.call_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_not_triggered_by_keyerror(
        self, network_manager, fake_matrix_portal
    ):
        """Test that KeyError does not trigger circuit breaker."""
        fake_matrix_portal.get_io_feed = MagicMock(side_effect=KeyError("Missing key"))

        result = await network_manager.get_left_team_score()

        assert result is None
        assert network_manager._circuit_breaker_open_until is None

    @pytest.mark.asyncio
    async def test_circuit_breaker_not_triggered_by_typeerror(
        self, network_manager, fake_matrix_portal
    ):
        """Test that TypeError does not trigger circuit breaker."""
        fake_matrix_portal.get_io_feed = MagicMock(side_effect=TypeError("Type error"))

        result = await network_manager.get_left_team_score()

        assert result is None
        assert network_manager._circuit_breaker_open_until is None

    @pytest.mark.asyncio
    async def test_show_connecting_not_called_when_circuit_breaker_open(
        self, network_manager, fake_matrix_portal
    ):
        """Test that show_connecting is not called when circuit breaker is open."""
        mock_show_connecting = MagicMock()
        network_manager.display_manager.show_connecting = mock_show_connecting
        network_manager._circuit_breaker_open_until = time.monotonic() + 60

        await network_manager.get_left_team_score()

        assert mock_show_connecting.call_count == 0
