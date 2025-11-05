"""Tests for GameController using real manager instances."""

from unittest.mock import patch

import pytest

from fakes import FakeMatrixPortal
from lib.display_manager import DisplayManager
from lib.game_controller import GameController
from lib.network_manager import NetworkManager
from lib.score_manager import ScoreManager


class TestGameControllerOnlineMode:
    """Test GameController with successful network operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures with real managers."""
        self.fake_portal = FakeMatrixPortal()
        self.network_manager = NetworkManager(self.fake_portal)
        self.score_manager = ScoreManager(self.network_manager)
        self.display_manager = DisplayManager(self.fake_portal)

        self.game_controller = GameController(
            self.score_manager,
            self.display_manager,
            self.network_manager,
        )

    def test_initialization(self):
        """Test that GameController initializes."""
        assert self.game_controller is not None

    @pytest.mark.asyncio
    async def test_handle_left_score_button_increments_and_pushes(self):
        """Test that left score button actually increments and pushes to network."""
        # Initial state
        assert self.score_manager.left_score == 0

        # Press button
        await self.game_controller.handle_left_score_button()

        # Verify score incremented
        assert self.score_manager.left_score == 1

        # Verify score was pushed to network
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 1
        )

    @pytest.mark.asyncio
    async def test_handle_right_score_button_increments_and_pushes(self):
        """Test that right score button actually increments and pushes to network."""
        # Initial state
        assert self.score_manager.right_score == 0

        # Press button
        await self.game_controller.handle_right_score_button()

        # Verify score incremented
        assert self.score_manager.right_score == 1

        # Verify score was pushed to network
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED)
            == 1
        )

    @pytest.mark.asyncio
    async def test_handle_multiple_button_presses(self):
        """Test multiple button presses increment correctly."""
        # Press left button 3 times
        await self.game_controller.handle_left_score_button()
        await self.game_controller.handle_left_score_button()
        await self.game_controller.handle_left_score_button()

        # Press right button 2 times
        await self.game_controller.handle_right_score_button()
        await self.game_controller.handle_right_score_button()

        # Verify final scores (local updates work immediately)
        assert self.score_manager.left_score == 3
        assert self.score_manager.right_score == 2

        # Force final sync to push all pending changes
        self.score_manager._last_sync_attempt = 0
        await self.score_manager.try_sync_scores()

        # Verify network has latest values
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 3
        )
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED)
            == 2
        )

    @pytest.mark.asyncio
    async def test_update_from_network_fetches_scores(self):
        """Test that update_from_network actually fetches from network."""
        # Set scores in network
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 7)

        # Update from network
        await self.game_controller.update_from_network()

        # Verify scores updated
        assert self.score_manager.left_score == 10
        assert self.score_manager.right_score == 7

    @pytest.mark.asyncio
    async def test_update_from_network_updates_team_names_on_score_change(self):
        """Test that team names are fetched when scores change."""
        # Set initial scores
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        await self.game_controller.update_from_network()

        # Set team names and change scores
        self.fake_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Warriors")
        self.fake_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Dragons")
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)

        # Update from network
        await self.game_controller.update_from_network()

        # Verify scores updated
        assert self.score_manager.left_score == 6
        assert self.score_manager.right_score == 3

    @pytest.mark.asyncio
    async def test_update_team_names_with_custom_names(self):
        """Test that update_team_names fetches and uses custom team names."""
        # Set team names in network
        self.fake_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Phoenix")
        self.fake_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Tigers")

        # Update team names
        await self.game_controller.update_team_names()

        # Verify team names were fetched
        assert await self.network_manager.get_left_team_name() == "Phoenix"
        assert await self.network_manager.get_right_team_name() == "Tigers"

    @pytest.mark.asyncio
    async def test_update_team_names_uses_defaults_when_not_set(self):
        """Test that update_team_names uses defaults when network has no values."""
        # Don't set any team names in network (they'll be None)

        # Update team names
        await self.game_controller.update_team_names()

        # Verify defaults are used
        assert await self.network_manager.get_left_team_name() == "AWAY"
        assert await self.network_manager.get_right_team_name() == "HOME"

    @pytest.mark.asyncio
    async def test_button_press_with_existing_scores(self):
        """Test button press increments from existing score."""
        # Set initial score in network
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        await self.game_controller.update_from_network()

        # Press button
        await self.game_controller.handle_left_score_button()

        # Verify score incremented from existing value
        assert self.score_manager.left_score == 11
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED)
            == 11
        )

    @pytest.mark.asyncio
    async def test_full_game_workflow(self):
        """Test a complete game workflow."""
        # Initialize with team names
        self.fake_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "AWAY")
        self.fake_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "HOME")
        await self.game_controller.update_team_names()

        # Simulate a game with button presses
        await self.game_controller.handle_left_score_button()  # AWAY: 1, HOME: 0
        await self.game_controller.handle_right_score_button()  # AWAY: 1, HOME: 1
        await self.game_controller.handle_left_score_button()  # AWAY: 2, HOME: 1
        await self.game_controller.handle_left_score_button()  # AWAY: 3, HOME: 1

        # Verify final state
        assert self.score_manager.left_score == 3
        assert self.score_manager.right_score == 1

        # Wait for pending changes to sync before fetching network updates
        self.score_manager._last_sync_attempt = 0
        await self.score_manager.try_sync_scores()

        # Simulate another device updating scores via network
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 2)
        await self.game_controller.update_from_network()

        # Verify scores synchronized
        assert self.score_manager.left_score == 3
        assert self.score_manager.right_score == 2


class TestGameControllerOfflineMode:
    """Test GameController behavior during network failures and offline operation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures with real managers."""
        self.fake_portal = FakeMatrixPortal()
        self.network_manager = NetworkManager(self.fake_portal)
        self.score_manager = ScoreManager(self.network_manager)
        self.display_manager = DisplayManager(self.fake_portal)

        self.game_controller = GameController(
            self.score_manager,
            self.display_manager,
            self.network_manager,
        )

    @pytest.mark.asyncio
    async def test_async_button_press_with_network_failure(self):
        """Test that button press works even when network sync fails."""
        assert self.score_manager.left_score == 0

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            await self.game_controller.handle_left_score_button()

        assert self.score_manager.left_score == 1
        assert self.score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_async_network_update_respects_pending_sync(self):
        """Test that network update doesn't overwrite pending local changes."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 5)

        self.score_manager.increment_left_score()
        self.score_manager.increment_left_score()
        assert self.score_manager.left_score == 2

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            await self.game_controller.update_from_network()

        assert self.score_manager.left_score == 2

    @pytest.mark.asyncio
    async def test_async_button_press_successful_sync(self):
        """Test async button press with successful network sync."""
        await self.game_controller.handle_left_score_button()

        assert self.score_manager.left_score == 1
        assert not self.score_manager.has_pending_changes()
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 1
        )

    @pytest.mark.asyncio
    async def test_async_update_team_names(self):
        """Test async team names update."""
        self.fake_portal.set_feed_value(
            NetworkManager.TEAM_LEFT_TEAM_FEED, "Async Team"
        )
        self.fake_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Warriors")

        await self.game_controller.update_team_names()

        assert await self.network_manager.get_left_team_name() == "Async Team"
        assert await self.network_manager.get_right_team_name() == "Warriors"

    @pytest.mark.asyncio
    async def test_async_update_from_network(self):
        """Test async network update."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 15)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 12)

        await self.game_controller.update_from_network()

        assert self.score_manager.left_score == 15
        assert self.score_manager.right_score == 12


class TestGameControllerWorkflows:
    """Test complex multi-step GameController workflows."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures with real managers."""
        self.fake_portal = FakeMatrixPortal()
        self.network_manager = NetworkManager(self.fake_portal)
        self.score_manager = ScoreManager(self.network_manager)
        self.display_manager = DisplayManager(self.fake_portal)

        self.game_controller = GameController(
            self.score_manager,
            self.display_manager,
            self.network_manager,
        )

    @pytest.mark.asyncio
    async def test_offline_mode_preserves_local_changes(self):
        """Test that local changes are preserved when network is unavailable."""
        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network unavailable"),
        ):
            await self.game_controller.handle_left_score_button()
            await self.game_controller.handle_left_score_button()
            await self.game_controller.handle_left_score_button()

        assert self.score_manager.left_score == 3
        assert self.score_manager.has_pending_changes()

        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 5)

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Still offline"),
        ):
            await self.game_controller.update_from_network()

        assert self.score_manager.left_score == 3
        assert self.score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_sync_retry_after_connection_restored(self):
        """Test that pending changes sync after network connection is restored."""
        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Network unavailable"),
        ):
            await self.game_controller.handle_left_score_button()
            await self.game_controller.handle_left_score_button()

        assert self.score_manager.left_score == 2
        assert self.score_manager.has_pending_changes()

        self.score_manager._last_sync_attempt = 0
        success = await self.score_manager.try_sync_scores()
        assert success
        assert not self.score_manager.has_pending_changes()
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 2
        )

    @pytest.mark.asyncio
    async def test_exponential_backoff_in_integration(self):
        """Test exponential backoff in a realistic scenario."""
        initial_delay = self.score_manager.get_next_retry_delay()
        assert initial_delay == 1.0

        with patch.object(
            self.network_manager,
            "set_right_team_score",
            side_effect=Exception("Network error"),
        ):
            await self.game_controller.handle_right_score_button()

        assert self.score_manager.has_pending_changes()
        assert self.score_manager.get_next_retry_delay() == 2.0

        with patch.object(
            self.network_manager,
            "set_right_team_score",
            side_effect=Exception("Network error"),
        ):
            self.score_manager._last_sync_attempt = 0
            await self.score_manager.try_sync_scores()

        assert self.score_manager.get_next_retry_delay() == 4.0

    @pytest.mark.asyncio
    async def test_multiple_offline_button_presses_then_sync(self):
        """Test multiple button presses offline followed by successful sync."""
        with (
            patch.object(
                self.network_manager,
                "set_left_team_score",
                side_effect=Exception("Offline"),
            ),
            patch.object(
                self.network_manager,
                "set_right_team_score",
                side_effect=Exception("Offline"),
            ),
        ):
            await self.game_controller.handle_left_score_button()
            await self.game_controller.handle_left_score_button()
            await self.game_controller.handle_left_score_button()
            await self.game_controller.handle_right_score_button()
            await self.game_controller.handle_right_score_button()

        assert self.score_manager.left_score == 3
        assert self.score_manager.right_score == 2
        assert self.score_manager.has_pending_changes()

        self.score_manager._last_sync_attempt = 0
        success = await self.score_manager.try_sync_scores()
        assert success
        assert not self.score_manager.has_pending_changes()
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 3
        )
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED)
            == 2
        )

    @pytest.mark.asyncio
    async def test_partial_network_failure(self):
        """Test scenario where one score syncs but the other fails."""
        self.score_manager.increment_left_score()
        self.score_manager.increment_right_score()

        with patch.object(
            self.network_manager,
            "set_right_team_score",
            side_effect=Exception("Network error on right"),
        ):
            success = await self.score_manager.try_sync_scores()

        assert not success
        assert self.score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_network_recovery_workflow(self):
        """Test complete offline-to-online workflow."""
        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Offline"),
        ):
            await self.game_controller.handle_left_score_button()
            assert self.score_manager.has_pending_changes()

        backoff_delay = self.score_manager.get_next_retry_delay()
        assert backoff_delay == 2.0

        self.score_manager._last_sync_attempt = 0
        success = await self.score_manager.try_sync_scores()
        assert success
        assert not self.score_manager.has_pending_changes()

        assert self.score_manager.get_next_retry_delay() == 1.0

        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        await self.game_controller.update_from_network()
        assert self.score_manager.left_score == 5

    @pytest.mark.asyncio
    async def test_concurrent_updates_local_wins(self):
        """Test that local updates take precedence over network when pending."""
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 100)

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Offline"),
        ):
            await self.game_controller.handle_left_score_button()
            await self.game_controller.handle_left_score_button()

        assert self.score_manager.left_score == 2

        with patch.object(
            self.network_manager,
            "set_left_team_score",
            side_effect=Exception("Still offline"),
        ):
            await self.game_controller.update_from_network()

        assert self.score_manager.left_score == 2

        self.score_manager._last_sync_attempt = 0
        success = await self.score_manager.try_sync_scores()
        assert success
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 2
        )
