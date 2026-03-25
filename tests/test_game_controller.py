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
    async def test_gender_matchup_cycles_through_button_presses(
        self, game_controller, display_manager
    ):
        """Test that gender matchup cycles correctly through multiple button presses."""
        await game_controller.update_team_names()
        game_controller.initialize_scores()

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


class TestGameControllerDisplayMethods:
    """Test GameController display update methods."""

    def test_set_team_names(self, game_controller, display_manager):
        """Test that set_team_names updates display correctly."""
        game_controller.set_team_names("Phoenix", "Tigers")

        left_label = display_manager.text_elements["left_team"]["label"]
        right_label = display_manager.text_elements["right_team"]["label"]

        assert left_label.text == "Phoenix"
        assert right_label.text == "Tigers"

    def test_initialize_scores(self, game_controller, display_manager, score_manager):
        """Test that initialize_scores updates score display and gender matchup."""
        # Set some scores
        score_manager.left_score = 3
        score_manager.right_score = 2

        # Initialize scores
        game_controller.initialize_scores()

        # Verify scores are displayed
        left_score_label = display_manager.text_elements["left_team_score"]["label"]
        right_score_label = display_manager.text_elements["right_team_score"]["label"]

        assert left_score_label.text == "3"
        assert right_score_label.text == "2"

        # Verify gender matchup is updated (sum=5, 5%4=1, WMP start → MMP1)
        matchup_label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]

        assert matchup_label.text == "MMP"
        assert counter_label.text == "1"


class TestHandleResetButton:
    """Test GameController reset button handler."""

    @pytest.mark.asyncio
    async def test_handle_reset_button_zeroes_display(
        self, game_controller, display_manager, score_manager
    ):
        """Test that handle_reset_button resets scores to 0-0 on display."""
        game_controller.initialize_scores()

        # Score some points
        await game_controller.handle_left_score_button()
        await game_controller.handle_left_score_button()
        await game_controller.handle_right_score_button()

        assert score_manager.left_score == 2
        assert score_manager.right_score == 1

        # Reset
        await game_controller.handle_reset_button()

        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

        left_label = display_manager.text_elements["left_team_score"]["label"]
        right_label = display_manager.text_elements["right_team_score"]["label"]
        assert left_label.text == "0"
        assert right_label.text == "0"

    @pytest.mark.asyncio
    async def test_handle_reset_button_resets_gender_matchup(
        self, game_controller, display_manager
    ):
        """Test that after reset, gender matchup reflects score sum of 0."""
        game_controller.initialize_scores()

        # Score some points to change matchup
        await game_controller.handle_left_score_button()
        await game_controller.handle_right_score_button()

        # Reset
        await game_controller.handle_reset_button()

        matchup_label = display_manager.text_elements["gender_matchup"]["label"]
        counter_label = display_manager.text_elements["gender_matchup_counter"]["label"]
        assert matchup_label.text == "WMP"
        assert counter_label.text == "2"


class TestHandleUndoAfterReset:
    """Test GameController undo after reset."""

    @pytest.mark.asyncio
    async def test_undo_after_reset_restores_both_scores_on_display(
        self, game_controller, display_manager, score_manager
    ):
        """Test that undoing a reset updates both score displays."""
        game_controller.initialize_scores()

        await game_controller.handle_left_score_button()
        await game_controller.handle_left_score_button()
        await game_controller.handle_right_score_button()

        assert score_manager.left_score == 2
        assert score_manager.right_score == 1

        await game_controller.handle_reset_button()
        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

        await game_controller.handle_undo_button()
        assert score_manager.left_score == 2
        assert score_manager.right_score == 1

        left_label = display_manager.text_elements["left_team_score"]["label"]
        right_label = display_manager.text_elements["right_team_score"]["label"]
        assert left_label.text == "2"
        assert right_label.text == "1"


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

        # Verify final scores
        assert score_manager.left_score == 3
        assert score_manager.right_score == 2

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
    async def test_update_team_names_updates_display(
        self, display_manager, fake_matrix_portal, game_controller
    ):
        """Test that update_team_names updates the display with fetched team names."""
        # Set team names in network
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Phoenix")
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Tigers")

        # Update team names
        await game_controller.update_team_names()

        # Verify display is updated
        left_label = display_manager.text_elements["left_team"]["label"]
        right_label = display_manager.text_elements["right_team"]["label"]

        assert left_label.text == "Phoenix"
        assert right_label.text == "Tigers"

    @pytest.mark.asyncio
    async def test_full_game_workflow(
        self, display_manager, fake_matrix_portal, game_controller, score_manager
    ):
        """Test a complete game workflow."""
        # Initialize with team names
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "AWAY")
        fake_matrix_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "HOME")
        await game_controller.update_team_names()
        game_controller.initialize_scores()

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
