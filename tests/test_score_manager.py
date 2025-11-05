"""Tests for ScoreManager using fake implementations."""

import time
from unittest.mock import AsyncMock, patch

import pytest

from fakes import FakeMatrixPortal
from lib.network_manager import NetworkManager
from lib.score_manager import ScoreManager


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
        assert self.score_manager.left_score == 0
        assert self.score_manager.right_score == 0

    @pytest.mark.asyncio
    async def test_update_scores_with_initial_values(self):
        """Test updating scores with initial values."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        changed = await self.score_manager.update_scores()

        assert self.score_manager.left_score == 5
        assert self.score_manager.right_score == 3
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_detects_left_score_change(self):
        """Test that update_scores returns True when left score changes."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await self.score_manager.update_scores()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)
        changed = await self.score_manager.update_scores()

        assert self.score_manager.left_score == 6
        assert self.score_manager.right_score == 3
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_detects_right_score_change(self):
        """Test that update_scores returns True when right score changes."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await self.score_manager.update_scores()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 4)
        changed = await self.score_manager.update_scores()

        assert self.score_manager.left_score == 5
        assert self.score_manager.right_score == 4
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_detects_both_scores_change(self):
        """Test that update_scores returns True when both scores change."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await self.score_manager.update_scores()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 4)
        changed = await self.score_manager.update_scores()

        assert self.score_manager.left_score == 6
        assert self.score_manager.right_score == 4
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_no_change_when_scores_same(self):
        """Test that update_scores returns False when scores don't change."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await self.score_manager.update_scores()

        changed = await self.score_manager.update_scores()

        assert self.score_manager.left_score == 5
        assert self.score_manager.right_score == 3
        assert not changed

    @pytest.mark.asyncio
    async def test_update_scores_with_string_values(self):
        """Test that update_scores handles string score values."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, "10")
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, "7")

        changed = await self.score_manager.update_scores()

        assert self.score_manager.left_score == 10
        assert self.score_manager.right_score == 7
        assert changed

    @pytest.mark.asyncio
    async def test_update_scores_multiple_updates(self):
        """Test multiple score updates in sequence."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 0)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 0)
        await self.score_manager.update_scores()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 1)
        changed1 = await self.score_manager.update_scores()
        assert changed1

        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 1)
        changed2 = await self.score_manager.update_scores()
        assert changed2

        changed3 = await self.score_manager.update_scores()
        assert not changed3


class TestScoreManagerPendingSync:
    """Test ScoreManager pending sync flag and exponential backoff retry logic."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.fake_portal = FakeMatrixPortal()
        self.network_manager = NetworkManager(self.fake_portal)
        self.score_manager = ScoreManager(self.network_manager)

    def test_increment_sets_pending_sync_flag(self):
        """Test that incrementing score sets the pending sync flag."""
        assert not self.score_manager.has_pending_changes()

        self.score_manager.increment_left_score()
        assert self.score_manager.has_pending_changes()
        assert self.score_manager.left_score == 1

    @pytest.mark.asyncio
    async def test_successful_sync_clears_pending_flag(self):
        """Test that successful sync clears the pending sync flag."""
        self.score_manager.increment_left_score()
        assert self.score_manager.has_pending_changes()

        success = await self.score_manager.try_sync_scores()
        assert success
        assert not self.score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_failed_sync_keeps_pending_flag(self):
        """Test that failed sync keeps the pending sync flag set."""
        self.score_manager.increment_left_score()

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            success = await self.score_manager.try_sync_scores()
            assert not success
            assert self.score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_update_scores_skips_network_when_pending_sync(self):
        """Test that update_scores skips network fetch when there are pending changes."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 5)

        self.score_manager.increment_left_score()
        assert self.score_manager.left_score == 1
        assert self.score_manager.has_pending_changes()

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            changed = await self.score_manager.update_scores()
            assert not changed
            assert self.score_manager.left_score == 1

    @pytest.mark.asyncio
    async def test_update_scores_fetches_when_no_pending_sync(self):
        """Test that update_scores fetches from network when no pending changes."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 7)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        assert not self.score_manager.has_pending_changes()
        changed = await self.score_manager.update_scores()

        assert changed
        assert self.score_manager.left_score == 7
        assert self.score_manager.right_score == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that retry delay follows exponential backoff pattern."""
        self.score_manager.increment_left_score()

        assert self.score_manager.get_next_retry_delay() == 1.0

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 2.0

            self.score_manager._last_sync_attempt = 0
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 4.0

            self.score_manager._last_sync_attempt = 0
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 8.0

            self.score_manager._last_sync_attempt = 0
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 16.0

            self.score_manager._last_sync_attempt = 0
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 32.0

            self.score_manager._last_sync_attempt = 0
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 60.0

            self.score_manager._last_sync_attempt = 0
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 60.0

    @pytest.mark.asyncio
    async def test_backoff_resets_after_successful_sync(self):
        """Test that backoff delay resets after a successful sync."""
        self.score_manager.increment_left_score()

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 2.0

            self.score_manager._last_sync_attempt = 0
            await self.score_manager.try_sync_scores()
            assert self.score_manager.get_next_retry_delay() == 4.0

        self.score_manager.increment_right_score()
        self.score_manager._last_sync_attempt = 0
        success = await self.score_manager.try_sync_scores()
        assert success
        assert self.score_manager.get_next_retry_delay() == 1.0

    @pytest.mark.asyncio
    async def test_concurrent_local_and_network_updates(self):
        """Test behavior when local changes are made while network has different values."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        self.score_manager.increment_left_score()
        self.score_manager.increment_left_score()
        assert self.score_manager.left_score == 2
        assert self.score_manager.has_pending_changes()

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            changed = await self.score_manager.update_scores()
            assert not changed
            assert self.score_manager.left_score == 2

        self.score_manager._last_sync_attempt = 0
        success = await self.score_manager.try_sync_scores()
        assert success
        assert not self.score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_sync_only_changed_scores(self):
        """Test that try_sync_scores only syncs scores that have changed."""
        self.score_manager.increment_left_score()

        with (
            patch.object(self.network_manager, "set_left_team_score") as mock_left,
            patch.object(self.network_manager, "set_right_team_score") as mock_right,
        ):
            await self.score_manager.try_sync_scores()

            mock_left.assert_called_once_with(1)
            mock_right.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_delay_prevents_immediate_retry(self):
        """Test that retry delay prevents sync attempts before delay expires."""
        self.score_manager.increment_left_score()

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            result1 = await self.score_manager.try_sync_scores()
            assert not result1

            result2 = await self.score_manager.try_sync_scores()
            assert not result2

            assert self.score_manager.has_pending_changes()
