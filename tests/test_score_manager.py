"""Tests for ScoreManager using fake implementations."""

import time
from unittest.mock import AsyncMock, patch

import pytest

from lib.network_manager import NetworkManager


class TestScoreManager:
    """Test ScoreManager with fake hardware."""

    def test_initialization(self, score_manager):
        """Test that ScoreManager initializes without errors."""
        assert score_manager is not None
        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

    @pytest.mark.asyncio
    async def test_update_scores_with_initial_values(self, score_manager, fake_matrix_portal):
        """Test updating scores with initial values."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        changed = await score_manager.update_scores()

        assert score_manager.left_score == 5
        assert score_manager.right_score == 3
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_detects_left_score_change(self, score_manager, fake_matrix_portal):
        """Test that update_scores returns True when left score changes."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await score_manager.update_scores()

        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)
        changed = await score_manager.update_scores()

        assert score_manager.left_score == 6
        assert score_manager.right_score == 3
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_detects_right_score_change(
        self, score_manager, fake_matrix_portal
    ):
        """Test that update_scores returns True when right score changes."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await score_manager.update_scores()

        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 4)
        changed = await score_manager.update_scores()

        assert score_manager.left_score == 5
        assert score_manager.right_score == 4
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_detects_both_scores_change(
        self, score_manager, fake_matrix_portal
    ):
        """Test that update_scores returns True when both scores change."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await score_manager.update_scores()

        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 4)
        changed = await score_manager.update_scores()

        assert score_manager.left_score == 6
        assert score_manager.right_score == 4
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_no_change_when_scores_same(
        self, score_manager, fake_matrix_portal
    ):
        """Test that update_scores returns False when scores don't change."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await score_manager.update_scores()

        changed = await score_manager.update_scores()

        assert score_manager.left_score == 5
        assert score_manager.right_score == 3
        assert not changed

    @pytest.mark.asyncio
    async def test_update_scores_with_string_values(self, score_manager, fake_matrix_portal):
        """Test that update_scores handles string score values."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, "10")
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, "7")

        changed = await score_manager.update_scores()

        assert score_manager.left_score == 10
        assert score_manager.right_score == 7
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_multiple_updates(self, score_manager, fake_matrix_portal):
        """Test multiple score updates in sequence."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 0)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 0)
        await score_manager.update_scores()

        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 1)
        changed1 = await score_manager.update_scores()
        assert changed1

        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 1)
        changed2 = await score_manager.update_scores()
        assert changed2

        changed3 = await score_manager.update_scores()
        assert not changed3


class TestScoreManagerPendingSync:
    """Test ScoreManager pending sync flag and exponential backoff retry logic."""

    def test_increment_sets_pending_sync_flag(self, score_manager):
        """Test that incrementing score sets the pending sync flag."""
        assert not score_manager.has_pending_changes()

        score_manager.increment_left_score()
        assert score_manager.has_pending_changes()
        assert score_manager.left_score == 1

    @pytest.mark.asyncio
    async def test_successful_sync_clears_pending_flag(self, score_manager):
        """Test that successful sync clears the pending sync flag."""
        score_manager.increment_left_score()
        assert score_manager.has_pending_changes()

        success = await score_manager.try_sync_scores()
        assert success
        assert not score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_failed_sync_keeps_pending_flag(self, score_manager, network_manager):
        """Test that failed sync keeps the pending sync flag set."""
        score_manager.increment_left_score()

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            success = await score_manager.try_sync_scores()
            assert not success
            assert score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_update_scores_skips_network_when_pending_sync(
        self, score_manager, fake_matrix_portal, network_manager
    ):
        """Test that update_scores skips network fetch when there are pending changes."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 5)

        score_manager.increment_left_score()
        assert score_manager.left_score == 1
        assert score_manager.has_pending_changes()

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            changed = await score_manager.update_scores()
            assert not changed
            assert score_manager.left_score == 1

    @pytest.mark.asyncio
    async def test_update_scores_fetches_when_no_pending_sync(
        self, score_manager, fake_matrix_portal
    ):
        """Test that update_scores fetches from network when no pending changes."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 7)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        assert not score_manager.has_pending_changes()
        changed = await score_manager.update_scores()

        assert changed
        assert score_manager.left_score == 7
        assert score_manager.right_score == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self, score_manager, network_manager):
        """Test that retry delay follows exponential backoff pattern."""
        score_manager.increment_left_score()

        assert score_manager.get_next_retry_delay() == 1.0

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 2.0

            score_manager._last_sync_attempt = 0
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 4.0

            score_manager._last_sync_attempt = 0
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 8.0

            score_manager._last_sync_attempt = 0
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 16.0

            score_manager._last_sync_attempt = 0
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 32.0

            score_manager._last_sync_attempt = 0
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 60.0

            score_manager._last_sync_attempt = 0
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 60.0

    @pytest.mark.asyncio
    async def test_backoff_resets_after_successful_sync(self, score_manager, network_manager):
        """Test that backoff delay resets after a successful sync."""
        score_manager.increment_left_score()

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 2.0

            score_manager._last_sync_attempt = 0
            await score_manager.try_sync_scores()
            assert score_manager.get_next_retry_delay() == 4.0

        score_manager.increment_right_score()
        score_manager._last_sync_attempt = 0
        success = await score_manager.try_sync_scores()
        assert success
        assert score_manager.get_next_retry_delay() == 1.0

    @pytest.mark.asyncio
    async def test_concurrent_local_and_network_updates(
        self, score_manager, fake_matrix_portal, network_manager
    ):
        """Test behavior when local changes are made while network has different values."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        score_manager.increment_left_score()
        score_manager.increment_left_score()
        assert score_manager.left_score == 2
        assert score_manager.has_pending_changes()

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            changed = await score_manager.update_scores()
            assert not changed
            assert score_manager.left_score == 2

        score_manager._last_sync_attempt = 0
        success = await score_manager.try_sync_scores()
        assert success
        assert not score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_sync_only_changed_scores(self, score_manager, network_manager):
        """Test that try_sync_scores only syncs scores that have changed."""
        score_manager.increment_left_score()

        with (
            patch.object(network_manager, "set_left_team_score") as mock_left,
            patch.object(network_manager, "set_right_team_score") as mock_right,
        ):
            await score_manager.try_sync_scores()

            mock_left.assert_called_once_with(1)
            mock_right.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_delay_prevents_immediate_retry(self, score_manager, network_manager):
        """Test that retry delay prevents sync attempts before delay expires."""
        score_manager.increment_left_score()

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            result1 = await score_manager.try_sync_scores()
            assert not result1

            result2 = await score_manager.try_sync_scores()
            assert not result2

            assert score_manager.has_pending_changes()
