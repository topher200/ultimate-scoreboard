"""Tests for GameController using real manager instances."""

import pytest

from fakes import FakeMatrixPortal
from lib.display_manager import DisplayManager
from lib.game_controller import GameController
from lib.network_manager import NetworkManager
from lib.score_manager import ScoreManager


class TestGameController:
    """Test GameController with real manager instances and fake hardware."""

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

    def test_handle_left_score_button_increments_and_pushes(self):
        """Test that left score button actually increments and pushes to network."""
        # Initial state
        assert self.score_manager.left_score == 0

        # Press button
        self.game_controller.handle_left_score_button()

        # Verify score incremented
        assert self.score_manager.left_score == 1

        # Verify score was pushed to network
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 1
        )

    def test_handle_right_score_button_increments_and_pushes(self):
        """Test that right score button actually increments and pushes to network."""
        # Initial state
        assert self.score_manager.right_score == 0

        # Press button
        self.game_controller.handle_right_score_button()

        # Verify score incremented
        assert self.score_manager.right_score == 1

        # Verify score was pushed to network
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED)
            == 1
        )

    def test_handle_multiple_button_presses(self):
        """Test multiple button presses increment correctly."""
        # Press left button 3 times
        self.game_controller.handle_left_score_button()
        self.game_controller.handle_left_score_button()
        self.game_controller.handle_left_score_button()

        # Press right button 2 times
        self.game_controller.handle_right_score_button()
        self.game_controller.handle_right_score_button()

        # Verify final scores
        assert self.score_manager.left_score == 3
        assert self.score_manager.right_score == 2

        # Verify network has latest values
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED) == 3
        )
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED)
            == 2
        )

    def test_update_from_network_fetches_scores(self):
        """Test that update_from_network actually fetches from network."""
        # Set scores in network
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 7)

        # Update from network
        self.game_controller.update_from_network()

        # Verify scores updated
        assert self.score_manager.left_score == 10
        assert self.score_manager.right_score == 7

    def test_update_from_network_updates_team_names_on_score_change(self):
        """Test that team names are fetched when scores change."""
        # Set initial scores
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 5)
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 3)
        self.game_controller.update_from_network()

        # Set team names and change scores
        self.fake_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Warriors")
        self.fake_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Dragons")
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 6)

        # Update from network
        self.game_controller.update_from_network()

        # Verify scores updated
        assert self.score_manager.left_score == 6
        assert self.score_manager.right_score == 3

    def test_update_team_names_with_custom_names(self):
        """Test that update_team_names fetches and uses custom team names."""
        # Set team names in network
        self.fake_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "Phoenix")
        self.fake_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "Tigers")

        # Update team names
        self.game_controller.update_team_names()

        # Verify team names were fetched
        assert self.network_manager.get_left_team_name() == "Phoenix"
        assert self.network_manager.get_right_team_name() == "Tigers"

    def test_update_team_names_uses_defaults_when_not_set(self):
        """Test that update_team_names uses defaults when network has no values."""
        # Don't set any team names in network (they'll be None)

        # Update team names
        self.game_controller.update_team_names()

        # Verify defaults are used
        assert self.network_manager.get_left_team_name() == "AWAY"
        assert self.network_manager.get_right_team_name() == "HOME"

    def test_button_press_with_existing_scores(self):
        """Test button press increments from existing score."""
        # Set initial score in network
        self.fake_portal.set_feed_value(NetworkManager.SCORES_LEFT_TEAM_FEED, 10)
        self.game_controller.update_from_network()

        # Press button
        self.game_controller.handle_left_score_button()

        # Verify score incremented from existing value
        assert self.score_manager.left_score == 11
        assert (
            self.fake_portal.get_pushed_value(NetworkManager.SCORES_LEFT_TEAM_FEED)
            == 11
        )

    def test_full_game_workflow(self):
        """Test a complete game workflow."""
        # Initialize with team names
        self.fake_portal.set_feed_value(NetworkManager.TEAM_LEFT_TEAM_FEED, "AWAY")
        self.fake_portal.set_feed_value(NetworkManager.TEAM_RIGHT_TEAM_FEED, "HOME")
        self.game_controller.update_team_names()

        # Simulate a game with button presses
        self.game_controller.handle_left_score_button()  # AWAY: 1, HOME: 0
        self.game_controller.handle_right_score_button()  # AWAY: 1, HOME: 1
        self.game_controller.handle_left_score_button()  # AWAY: 2, HOME: 1
        self.game_controller.handle_left_score_button()  # AWAY: 3, HOME: 1

        # Verify final state
        assert self.score_manager.left_score == 3
        assert self.score_manager.right_score == 1

        # Simulate another device updating scores via network
        self.fake_portal.set_feed_value(NetworkManager.SCORES_RIGHT_TEAM_FEED, 2)
        self.game_controller.update_from_network()

        # Verify scores synchronized
        assert self.score_manager.left_score == 3
        assert self.score_manager.right_score == 2
