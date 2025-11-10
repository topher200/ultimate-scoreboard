"""Tests for GameController using real manager instances."""

from unittest.mock import patch

import pytest

from lib.network_manager import NetworkManager


class TestGenderMatchupCalculation:
    """Test gender matchup calculation based on score sum."""

    def test_calculate_gender_matchup_sum_0(self, game_controller):
        """Test gender matchup for score sum 0 (0-0) returns WMP2."""
        matchup, count = game_controller._calculate_gender_matchup(0)
        assert matchup == "WMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_1(self, game_controller):
        """Test gender matchup for score sum 1 (1-0 or 0-1) returns MMP1."""
        matchup, count = game_controller._calculate_gender_matchup(1)
        assert matchup == "MMP"
        assert count == 1

    def test_calculate_gender_matchup_sum_2(self, game_controller):
        """Test gender matchup for score sum 2 returns MMP2."""
        matchup, count = game_controller._calculate_gender_matchup(2)
        assert matchup == "MMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_3(self, game_controller):
        """Test gender matchup for score sum 3 returns WMP1."""
        matchup, count = game_controller._calculate_gender_matchup(3)
        assert matchup == "WMP"
        assert count == 1

    def test_calculate_gender_matchup_sum_4_cycle_repeats(self, game_controller):
        """Test gender matchup for score sum 4 returns WMP2 (cycle repeats)."""
        matchup, count = game_controller._calculate_gender_matchup(4)
        assert matchup == "WMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_5(self, game_controller):
        """Test gender matchup for score sum 5 returns MMP1."""
        matchup, count = game_controller._calculate_gender_matchup(5)
        assert matchup == "MMP"
        assert count == 1

    def test_calculate_gender_matchup_sum_6(self, game_controller):
        """Test gender matchup for score sum 6 returns MMP2."""
        matchup, count = game_controller._calculate_gender_matchup(6)
        assert matchup == "MMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_7(self, game_controller):
        """Test gender matchup for score sum 7 returns WMP1."""
        matchup, count = game_controller._calculate_gender_matchup(7)
        assert matchup == "WMP"
        assert count == 1

    def test_calculate_gender_matchup_large_sum(self, game_controller):
        """Test gender matchup calculation for large score sums."""
        # Test sum 20 (20 % 4 == 0)
        matchup, count = game_controller._calculate_gender_matchup(20)
        assert matchup == "WMP"
        assert count == 2

        # Test sum 21 (21 % 4 == 1)
        matchup, count = game_controller._calculate_gender_matchup(21)
        assert matchup == "MMP"
        assert count == 1

    @pytest.mark.asyncio
    async def test_update_team_names_sets_matchup_for_zero_score(
        self, game_controller, display_manager
    ):
        """Test that update_team_names sets gender matchup correctly for 0-0."""
        await game_controller.update_team_names()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"][
            "label"
        ]

        assert label.text == "WMP"
        assert counter_label.text == "2"

    @pytest.mark.asyncio
    async def test_button_press_updates_gender_matchup(self, game_controller, display_manager):
        """Test that pressing score button updates gender matchup display."""
        await game_controller.update_team_names()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"][
            "label"
        ]

        assert label.text == "WMP"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()

        assert label.text == "MMP"
        assert counter_label.text == "1"

    @pytest.mark.asyncio
    async def test_gender_matchup_cycles_through_button_presses(
        self, game_controller, display_manager
    ):
        """Test that gender matchup cycles correctly through multiple button presses."""
        await game_controller.update_team_names()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"][
            "label"
        ]

        assert label.text == "WMP"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()
        assert label.text == "MMP"
        assert counter_label.text == "1"

        await game_controller.handle_right_score_button()
        assert label.text == "MMP"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()
        assert label.text == "WMP"
        assert counter_label.text == "1"

        await game_controller.handle_right_score_button()
        assert label.text == "WMP"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()
        assert label.text == "MMP"
        assert counter_label.text == "1"

    @pytest.mark.asyncio
    async def test_network_update_recalculates_gender_matchup(
        self,
        game_controller,
        display_manager,
        score_manager,
        fake_matrix_portal,
    ):
        """Test that gender matchup is recalculated after network update."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 2)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 1)

        await game_controller.update_from_network()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"][
            "label"
        ]

        assert score_manager.left_score == 2
        assert score_manager.right_score == 1
        assert label.text == "WMP"
        assert counter_label.text == "1"


class TestGameControllerOnlineMode:
    """Test GameController with successful network operations."""

    def test_initialization(self, game_controller):
        """Test that GameController initializes."""
        assert game_controller is not None

    @pytest.mark.asyncio
    async def test_handle_left_score_button_increments_and_pushes(
        self, fake_matrix_portal, game_controller, score_manager
    ):
        """Test that left score button actually increments and pushes to network."""
        # Initial state
        assert score_manager.left_score == 0

        # Press button
        await game_controller.handle_left_score_button()

        # Verify score incremented
        assert score_manager.left_score == 1

        # Verify score was pushed to network
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 1
        )

    @pytest.mark.asyncio
    async def test_handle_right_score_button_increments_and_pushes(
        self, fake_matrix_portal, game_controller, score_manager
    ):
        """Test that right score button actually increments and pushes to network."""
        # Initial state
        assert score_manager.right_score == 0

        # Press button
        await game_controller.handle_right_score_button()

        # Verify score incremented
        assert score_manager.right_score == 1

        # Verify score was pushed to network
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED)
            == 1
        )

    @pytest.mark.asyncio
    async def test_handle_multiple_button_presses(
        self, fake_matrix_portal, game_controller, score_manager
    ):
        """Test multiple button presses increment correctly."""
        # Press left button 3 times
        await game_controller.handle_left_score_button()
        await game_controller.handle_left_score_button()
        await game_controller.handle_left_score_button()

        # Press right button 2 times
        await game_controller.handle_right_score_button()
        await game_controller.handle_right_score_button()

        # Verify final scores (local updates work immediately)
        assert score_manager.left_score == 3
        assert score_manager.right_score == 2

        # Force final sync to push all pending changes
        score_manager._last_sync_attempt = 0
        await score_manager.try_sync_scores()

        # Verify network has latest values
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 3
        )
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED)
            == 2
        )

    @pytest.mark.asyncio
    async def test_update_from_network_fetches_scores(
        self, fake_matrix_portal, game_controller, score_manager
    ):
        """Test that update_from_network actually fetches from network."""
        # Set scores in network
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 7)

        # Update from network
        await game_controller.update_from_network()

        # Verify scores updated
        assert score_manager.left_score == 10
        assert score_manager.right_score == 7

    @pytest.mark.asyncio
    async def test_update_from_network_updates_team_names_on_score_change(
        self,
        fake_matrix_portal,
        game_controller,
        network_manager,
        score_manager,
    ):
        """Test that team names are fetched when scores change."""
        # Set team names and scores
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Warriors")
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Dragons")
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)

        # Update from network
        await game_controller.update_from_network()

        # Verify scores updated
        assert score_manager.left_score == 6
        assert score_manager.right_score == 3
        # Verify team names were fetched
        assert await network_manager.get_left_team_name() == "Warriors"
        assert await network_manager.get_right_team_name() == "Dragons"

    @pytest.mark.asyncio
    async def test_update_team_names_with_custom_names(
        self, fake_matrix_portal, game_controller, network_manager
    ):
        """Test that update_team_names fetches and uses custom team names."""
        # Set team names in network
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Phoenix")
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Tigers")

        # Update team names
        await game_controller.update_team_names()

        # Verify team names were fetched
        assert await network_manager.get_left_team_name() == "Phoenix"
        assert await network_manager.get_right_team_name() == "Tigers"

    @pytest.mark.asyncio
    async def test_update_team_names_uses_defaults_when_not_set(
        self, game_controller, network_manager
    ):
        """Test that update_team_names uses defaults when network has no values."""
        # Don't set any team names in network (they'll be None)

        # Update team names
        await game_controller.update_team_names()

        # Verify defaults are used
        assert await network_manager.get_left_team_name() == "AWAY"
        assert await network_manager.get_right_team_name() == "HOME"

    @pytest.mark.asyncio
    async def test_button_press_with_existing_scores(
        self, fake_matrix_portal, game_controller, score_manager
    ):
        """Test button press increments from existing score."""
        # Set initial score in network
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        await game_controller.update_from_network()

        # Press button
        await game_controller.handle_left_score_button()

        # Verify score incremented from existing value
        assert score_manager.left_score == 11
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED)
            == 11
        )

    @pytest.mark.asyncio
    async def test_full_game_workflow(
        self, display_manager, fake_matrix_portal, game_controller, score_manager
    ):
        """Test a complete game workflow."""
        # Initialize with team names
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "AWAY")
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "HOME")
        await game_controller.update_team_names()

        # Get label references
        matchup_label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"][
            "label"
        ]

        # Verify initial state (0-0, sum=0) → WMP2
        assert matchup_label.text == "WMP"
        assert counter_label.text == "2"

        # Simulate a game with button presses
        await game_controller.handle_left_score_button()  # AWAY: 1, HOME: 0
        assert score_manager.left_score == 1
        assert score_manager.right_score == 0
        # sum=1 → MMP1
        assert matchup_label.text == "MMP"
        assert counter_label.text == "1"

        await game_controller.handle_right_score_button()  # AWAY: 1, HOME: 1
        assert score_manager.left_score == 1
        assert score_manager.right_score == 1
        # sum=2 → MMP2
        assert matchup_label.text == "MMP"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()  # AWAY: 2, HOME: 1
        assert score_manager.left_score == 2
        assert score_manager.right_score == 1
        # sum=3 → WMP1
        assert matchup_label.text == "WMP"
        assert counter_label.text == "1"

        await game_controller.handle_left_score_button()  # AWAY: 3, HOME: 1
        assert score_manager.left_score == 3
        assert score_manager.right_score == 1
        # sum=4 → WMP2
        assert matchup_label.text == "WMP"
        assert counter_label.text == "2"

        # Wait for pending changes to sync before fetching network updates
        score_manager._last_sync_attempt = 0
        await score_manager.try_sync_scores()

        # Simulate another device updating scores via network
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 2)
        await game_controller.update_from_network()

        # Verify scores synchronized
        assert score_manager.left_score == 3
        assert score_manager.right_score == 2
        # sum=5 → MMP1
        assert matchup_label.text == "MMP"
        assert counter_label.text == "1"


class TestGameControllerOfflineMode:
    """Test GameController behavior during network failures and offline operation."""

    @pytest.mark.asyncio
    async def test_async_button_press_with_network_failure(
        self, game_controller, network_manager, score_manager
    ):
        """Test that button press works even when network sync fails."""
        assert score_manager.left_score == 0

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            await game_controller.handle_left_score_button()

        assert score_manager.left_score == 1
        assert score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_async_network_update_respects_pending_sync(
        self,
        fake_matrix_portal,
        game_controller,
        network_manager,
        score_manager,
    ):
        """Test that network update doesn't overwrite pending local changes."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 5)

        score_manager.increment_left_score()
        score_manager.increment_left_score()
        assert score_manager.left_score == 2

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network error"),
        ):
            await game_controller.update_from_network()

        assert score_manager.left_score == 2

    @pytest.mark.asyncio
    async def test_async_button_press_successful_sync(
        self, fake_matrix_portal, game_controller, score_manager
    ):
        """Test async button press with successful network sync."""
        await game_controller.handle_left_score_button()

        assert score_manager.left_score == 1
        assert not score_manager.has_pending_changes()
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 1
        )

    @pytest.mark.asyncio
    async def test_async_update_team_names(
        self, fake_matrix_portal, game_controller, network_manager
    ):
        """Test async team names update."""
        fake_matrix_portal.set_feed_value(
            NetworkManager.TEAM_LEFT_TEAM_FEED, "Async Team"
        )
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Warriors")

        await game_controller.update_team_names()

        assert await network_manager.get_left_team_name() == "Async Team"
        assert await network_manager.get_right_team_name() == "Warriors"

    @pytest.mark.asyncio
    async def test_async_update_from_network(
        self, fake_matrix_portal, game_controller, score_manager
    ):
        """Test async network update."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 15)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 12)

        await game_controller.update_from_network()

        assert score_manager.left_score == 15
        assert score_manager.right_score == 12


class TestGameControllerWorkflows:
    """Test complex multi-step GameController workflows."""

    @pytest.mark.asyncio
    async def test_offline_mode_preserves_local_changes(
        self,
        fake_matrix_portal,
        game_controller,
        network_manager,
        score_manager,
    ):
        """Test that local changes are preserved when network is unavailable."""
        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network unavailable"),
        ):
            await game_controller.handle_left_score_button()
            await game_controller.handle_left_score_button()
            await game_controller.handle_left_score_button()

        assert score_manager.left_score == 3
        assert score_manager.has_pending_changes()

        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 5)

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Still offline"),
        ):
            await game_controller.update_from_network()

        assert score_manager.left_score == 3
        assert score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_sync_retry_after_connection_restored(
        self,
        fake_matrix_portal,
        game_controller,
        network_manager,
        score_manager,
    ):
        """Test that pending changes sync after network connection is restored."""
        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Network unavailable"),
        ):
            await game_controller.handle_left_score_button()
            await game_controller.handle_left_score_button()

        assert score_manager.left_score == 2
        assert score_manager.has_pending_changes()

        score_manager._last_sync_attempt = 0
        success = await score_manager.try_sync_scores()
        assert success
        assert not score_manager.has_pending_changes()
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 2
        )

    @pytest.mark.asyncio
    async def test_exponential_backoff_in_integration(
        self, game_controller, network_manager, score_manager
    ):
        """Test exponential backoff in a realistic scenario."""
        initial_delay = score_manager.get_next_retry_delay()
        assert initial_delay == 1.0

        with patch.object(
            network_manager,
            "set_right_team_score",
            side_effect=Exception("Network error"),
        ):
            await game_controller.handle_right_score_button()

        assert score_manager.has_pending_changes()
        assert score_manager.get_next_retry_delay() == 2.0

        with patch.object(
            network_manager,
            "set_right_team_score",
            side_effect=Exception("Network error"),
        ):
            score_manager._last_sync_attempt = 0
            await score_manager.try_sync_scores()

        assert score_manager.get_next_retry_delay() == 4.0

    @pytest.mark.asyncio
    async def test_multiple_offline_button_presses_then_sync(
        self,
        fake_matrix_portal,
        game_controller,
        network_manager,
        score_manager,
    ):
        """Test multiple button presses offline followed by successful sync."""
        with (
            patch.object(
                network_manager,
                "set_left_team_score",
                side_effect=Exception("Offline"),
            ),
            patch.object(
                network_manager,
                "set_right_team_score",
                side_effect=Exception("Offline"),
            ),
        ):
            await game_controller.handle_left_score_button()
            await game_controller.handle_left_score_button()
            await game_controller.handle_left_score_button()
            await game_controller.handle_right_score_button()
            await game_controller.handle_right_score_button()

        assert score_manager.left_score == 3
        assert score_manager.right_score == 2
        assert score_manager.has_pending_changes()

        score_manager._last_sync_attempt = 0
        success = await score_manager.try_sync_scores()
        assert success
        assert not score_manager.has_pending_changes()
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 3
        )
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED)
            == 2
        )

    @pytest.mark.asyncio
    async def test_partial_network_failure(self, network_manager, score_manager):
        """Test scenario where one score syncs but the other fails."""
        score_manager.increment_left_score()
        score_manager.increment_right_score()

        with patch.object(
            network_manager,
            "set_right_team_score",
            side_effect=Exception("Network error on right"),
        ):
            success = await score_manager.try_sync_scores()

        assert not success
        assert score_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_network_recovery_workflow(
        self,
        fake_matrix_portal,
        game_controller,
        network_manager,
        score_manager,
    ):
        """Test complete offline-to-online workflow."""
        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Offline"),
        ):
            await game_controller.handle_left_score_button()
            assert score_manager.has_pending_changes()

        backoff_delay = score_manager.get_next_retry_delay()
        assert backoff_delay == 2.0

        score_manager._last_sync_attempt = 0
        success = await score_manager.try_sync_scores()
        assert success
        assert not score_manager.has_pending_changes()

        assert score_manager.get_next_retry_delay() == 1.0

        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        await game_controller.update_from_network()
        assert score_manager.left_score == 5

    @pytest.mark.asyncio
    async def test_concurrent_updates_local_wins(
        self,
        fake_matrix_portal,
        game_controller,
        network_manager,
        score_manager,
    ):
        """Test that local updates take precedence over network when pending."""
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 100)

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Offline"),
        ):
            await game_controller.handle_left_score_button()
            await game_controller.handle_left_score_button()

        assert score_manager.left_score == 2

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Still offline"),
        ):
            await game_controller.update_from_network()

        assert score_manager.left_score == 2

        score_manager._last_sync_attempt = 0
        success = await score_manager.try_sync_scores()
        assert success
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 2
        )
