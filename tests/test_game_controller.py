"""Tests for GameController using real manager instances."""

from unittest.mock import patch

import pytest

from src.gender_manager import GenderManager
from src.network_manager import NetworkManager


class TestGenderMatchupCalculation:
    """Test gender matchup calculation based on score sum and starting gender."""

    def test_calculate_gender_matchup_sum_0_wmp(self, game_controller):
        """Test gender matchup for score sum 0 (0-0) with WMP start returns WMP2."""
        matchup, count = game_controller._calculate_gender_matchup(
            0, GenderManager.GENDER_WMP
        )
        assert matchup == "WMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_1_wmp(self, game_controller):
        """Test gender matchup for score sum 1 (1-0 or 0-1) with WMP start returns MMP1."""
        matchup, count = game_controller._calculate_gender_matchup(
            1, GenderManager.GENDER_WMP
        )
        assert matchup == "MMP"
        assert count == 1

    def test_calculate_gender_matchup_sum_2_wmp(self, game_controller):
        """Test gender matchup for score sum 2 with WMP start returns MMP2."""
        matchup, count = game_controller._calculate_gender_matchup(
            2, GenderManager.GENDER_WMP
        )
        assert matchup == "MMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_3_wmp(self, game_controller):
        """Test gender matchup for score sum 3 with WMP start returns WMP1."""
        matchup, count = game_controller._calculate_gender_matchup(
            3, GenderManager.GENDER_WMP
        )
        assert matchup == "WMP"
        assert count == 1

    def test_calculate_gender_matchup_sum_4_cycle_repeats_wmp(self, game_controller):
        """Test gender matchup for score sum 4 with WMP start returns WMP2 (cycle repeats)."""
        matchup, count = game_controller._calculate_gender_matchup(
            4, GenderManager.GENDER_WMP
        )
        assert matchup == "WMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_0_mmp(self, game_controller):
        """Test gender matchup for score sum 0 (0-0) with MMP start returns MMP2."""
        matchup, count = game_controller._calculate_gender_matchup(
            0, GenderManager.GENDER_MMP
        )
        assert matchup == "MMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_1_mmp(self, game_controller):
        """Test gender matchup for score sum 1 with MMP start returns WMP1."""
        matchup, count = game_controller._calculate_gender_matchup(
            1, GenderManager.GENDER_MMP
        )
        assert matchup == "WMP"
        assert count == 1

    def test_calculate_gender_matchup_sum_2_mmp(self, game_controller):
        """Test gender matchup for score sum 2 with MMP start returns WMP2."""
        matchup, count = game_controller._calculate_gender_matchup(
            2, GenderManager.GENDER_MMP
        )
        assert matchup == "WMP"
        assert count == 2

    def test_calculate_gender_matchup_sum_3_mmp(self, game_controller):
        """Test gender matchup for score sum 3 with MMP start returns MMP1."""
        matchup, count = game_controller._calculate_gender_matchup(
            3, GenderManager.GENDER_MMP
        )
        assert matchup == "MMP"
        assert count == 1

    def test_calculate_gender_matchup_sum_4_cycle_repeats_mmp(self, game_controller):
        """Test gender matchup for score sum 4 with MMP start returns MMP2 (cycle repeats)."""
        matchup, count = game_controller._calculate_gender_matchup(
            4, GenderManager.GENDER_MMP
        )
        assert matchup == "MMP"
        assert count == 2

    def test_calculate_gender_matchup_large_sum_wmp(self, game_controller):
        """Test gender matchup calculation for large score sums with WMP start."""
        # Test sum 20 (20 % 4 == 0)
        matchup, count = game_controller._calculate_gender_matchup(
            20, GenderManager.GENDER_WMP
        )
        assert matchup == "WMP"
        assert count == 2

        # Test sum 21 (21 % 4 == 1)
        matchup, count = game_controller._calculate_gender_matchup(
            21, GenderManager.GENDER_WMP
        )
        assert matchup == "MMP"
        assert count == 1

    @pytest.mark.asyncio
    async def test_update_team_names_sets_matchup_for_zero_score(
        self, game_controller, display_manager
    ):
        """Test that update_team_names sets gender matchup correctly for 0-0."""
        await game_controller.update_team_names_and_gender()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]

        assert label.text == "WMP"
        assert counter_label.text == "2"

    @pytest.mark.asyncio
    async def test_button_press_updates_gender_matchup(
        self, game_controller, display_manager
    ):
        """Test that pressing score button updates gender matchup display."""
        await game_controller.update_team_names_and_gender()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]

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
        await game_controller.update_team_names_and_gender()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]

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
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]

        assert score_manager.left_score == 2
        assert score_manager.right_score == 1
        assert label.text == "WMP"
        assert counter_label.text == "1"


class TestGameControllerKeepsScore:
    """Test GameController keeps score."""

    def test_initialization(self, game_controller):
        """Test that GameController initializes."""
        assert game_controller is not None

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
        await score_manager.try_sync_scores()

        # Verify network has latest values
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED)
            == 3
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
        fake_matrix_portal.set_feed_value(
            NetworkManager.TEAM_LEFT_TEAM_FEED, "Warriors"
        )
        fake_matrix_portal.set_feed_value(
            NetworkManager.TEAM_RIGHT_TEAM_FEED, "Dragons"
        )
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
        await game_controller.update_team_names_and_gender()

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
        await game_controller.update_team_names_and_gender()

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
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 0)
        await game_controller.update_from_network()

        # Press button
        await game_controller.handle_left_score_button()

        # Verify score incremented from existing value
        assert score_manager.left_score == 11

    @pytest.mark.asyncio
    async def test_full_game_workflow(
        self, display_manager, fake_matrix_portal, game_controller, score_manager
    ):
        """Test a complete game workflow."""
        # Initialize with team names
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "AWAY")
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "HOME")
        await game_controller.update_team_names_and_gender()

        # Get label references
        matchup_label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]

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


class TestGameControllerSyncsScores:
    """Test complex multi-step GameController workflows that sync scores."""

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

        success = await score_manager.try_sync_scores()
        assert success
        assert not score_manager.has_pending_changes()
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED)
            == 2
        )

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

        success = await score_manager.try_sync_scores()
        assert success
        assert not score_manager.has_pending_changes()
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED)
            == 3
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
        await game_controller.handle_left_score_button()
        assert score_manager.has_pending_changes()

        with patch.object(
            network_manager,
            "set_left_team_score",
            side_effect=Exception("Offline"),
        ):
            await score_manager.try_sync_scores()

        success = await score_manager.try_sync_scores()
        assert success
        assert not score_manager.has_pending_changes()

        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 0)
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

        success = await score_manager.try_sync_scores()
        assert success
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED)
            == 2
        )


class TestGenderFeedSupport:
    """Test gender feed support and local toggle functionality."""

    @pytest.mark.asyncio
    async def test_toggle_gender_button_changes_starting_gender(
        self, game_controller, display_manager, gender_manager
    ):
        """Test that toggle gender button changes starting gender and recalculates matchup."""
        # Initial state: WMP2 (default)
        await game_controller.update_team_names_and_gender()
        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]
        assert label.text == "WMP"
        assert counter_label.text == "2"
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP

        # Toggle to MMP
        await game_controller.handle_toggle_gender_button()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP
        assert label.text == "MMP"
        assert counter_label.text == "2"

        # Toggle back to WMP
        await game_controller.handle_toggle_gender_button()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP
        assert label.text == "WMP"
        assert counter_label.text == "2"

    @pytest.mark.asyncio
    async def test_toggle_gender_recalculates_matchup_for_current_score(
        self, game_controller, display_manager, gender_manager
    ):
        """Test that toggle gender recalculates matchup for current score sum."""
        # Set score to 1-0 (sum=1)
        await game_controller.handle_left_score_button()
        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]
        # With WMP start, sum=1 should be MMP1
        assert label.text == "MMP"
        assert counter_label.text == "1"

        # Toggle to MMP start
        await game_controller.handle_toggle_gender_button()
        # With MMP start, sum=1 should be WMP1
        assert label.text == "WMP"
        assert counter_label.text == "1"

    @pytest.mark.asyncio
    async def test_feed_based_gender_determination(
        self, game_controller, display_manager, fake_matrix_portal, gender_manager
    ):
        """Test that gender feed value determines starting gender."""
        # Set feed to 'mmp'
        fake_matrix_portal.set_feed_value(
            NetworkManager.FIRST_POINT_GENDER_FEED, GenderManager.GENDER_MMP
        )
        await game_controller.update_team_names_and_gender()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP
        assert label.text == "MMP"
        assert counter_label.text == "2"

        # Set feed to 'wmp'
        fake_matrix_portal.set_feed_value(
            NetworkManager.FIRST_POINT_GENDER_FEED, GenderManager.GENDER_WMP
        )
        await game_controller.update_team_names_and_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP
        assert label.text == "WMP"
        assert counter_label.text == "2"

    @pytest.mark.asyncio
    async def test_feed_gender_change_during_game_recalculates(
        self,
        game_controller,
        display_manager,
        fake_matrix_portal,
        score_manager,
        gender_manager,
    ):
        """Test that feed gender change during game immediately recalculates matchup."""
        # Set initial score
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 2)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 1)
        fake_matrix_portal.set_feed_value(
            NetworkManager.FIRST_POINT_GENDER_FEED, GenderManager.GENDER_WMP
        )
        await game_controller.update_from_network()

        label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]
        # With WMP start, sum=3 should be WMP1
        assert label.text == "WMP"
        assert counter_label.text == "1"

        # Change feed to 'mmp', and swap the scores so we refetch gender
        fake_matrix_portal.set_feed_value(
            NetworkManager.FIRST_POINT_GENDER_FEED, GenderManager.GENDER_MMP
        )
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 1)
        fake_matrix_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 2)
        await game_controller.update_from_network()

        # With MMP start, sum=3 should now be MMP1
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP
        assert label.text == "MMP"
        assert counter_label.text == "1"

    @pytest.mark.asyncio
    async def test_local_gender_toggle_queued_for_sync(
        self, game_controller, gender_manager, fake_matrix_portal
    ):
        """Test that local gender toggle is queued for network sync."""
        assert not gender_manager.has_pending_changes()

        await game_controller.handle_toggle_gender_button()
        assert gender_manager.has_pending_changes()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

        # Sync should push to network
        success = await gender_manager.try_sync_gender()
        assert success
        assert not gender_manager.has_pending_changes()
        assert (
            fake_matrix_portal.get_pushed_value(NetworkManager.FIRST_POINT_GENDER_FEED)
            == GenderManager.GENDER_MMP
        )

    @pytest.mark.asyncio
    async def test_local_gender_takes_precedence_until_sync(
        self, game_controller, gender_manager, fake_matrix_portal
    ):
        """Test that local gender value is trusted until successful sync."""
        # Toggle locally
        await game_controller.handle_toggle_gender_button()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

        # Set different value in network
        fake_matrix_portal.set_feed_value(
            NetworkManager.FIRST_POINT_GENDER_FEED, GenderManager.GENDER_WMP
        )

        # Update from network should skip due to pending changes
        with patch.object(
            gender_manager._network_manager,
            "set_first_point_gender",
            side_effect=Exception("Offline"),
        ):
            changed = await gender_manager.update_gender_from_network()
            assert not changed
            assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

        # After successful sync, network value should be used
        success = await gender_manager.try_sync_gender()
        assert success
        # Set feed to WMP again after sync (sync overwrote it with MMP)
        fake_matrix_portal.set_feed_value(
            NetworkManager.FIRST_POINT_GENDER_FEED, GenderManager.GENDER_WMP
        )
        # Now update from network should fetch the network value
        changed = await gender_manager.update_gender_from_network()
        assert changed
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP
