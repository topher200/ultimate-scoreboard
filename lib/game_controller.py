"""Coordinates game actions and state changes."""

from lib.display_manager import DisplayManager
from lib.network_manager import NetworkManager
from lib.score_manager import ScoreManager


class GameController:
    """Coordinates game actions between managers.

    Handles business logic for button presses, network updates, and display coordination.
    """

    def __init__(
        self,
        score_manager: ScoreManager,
        display_manager: DisplayManager,
        network_manager: NetworkManager,
    ):
        """Initialize GameController with manager dependencies.

        :param score_manager: ScoreManager instance for score operations
        :param display_manager: DisplayManager instance for display updates
        :param network_manager: NetworkManager instance for network operations
        """
        self._score_manager = score_manager
        self._display_manager = display_manager
        self._network_manager = network_manager

    def handle_left_score_button(self) -> None:
        """Handle left team score button press.
        
        Increments the left team score and updates the display.
        """
        print("UP button pressed! Incrementing left score...")
        self._display_manager.show_connecting(True)
        
        self._score_manager.increment_left_score()
        self._display_manager.set_text(
            "left_team_score", self._score_manager.left_score
        )
        print(f"Left score updated: {self._score_manager.left_score}")
        
        self._display_manager.show_connecting(False)

    def handle_right_score_button(self) -> None:
        """Handle right team score button press.
        
        Increments the right team score and updates the display.
        """
        print("DOWN button pressed! Incrementing right score...")
        self._display_manager.show_connecting(True)
        
        self._score_manager.increment_right_score()
        self._display_manager.set_text(
            "right_team_score", self._score_manager.right_score
        )
        print(f"Right score updated: {self._score_manager.right_score}")
        
        self._display_manager.show_connecting(False)

    def update_team_names(self) -> None:
        """Update team names and gender matchup from network.

        Fetches team names from the network and updates the display.
        """
        team_left_team = "AWAY"
        team_right_team = "HOME"
        gender_matchup = "WMP"
        gender_matchup_count = 1

        team_name = self._network_manager.get_left_team_name()
        if team_name is not None:
            print(f"Team {team_left_team} is now Team {team_name}")
            team_left_team = team_name

        team_name = self._network_manager.get_right_team_name()
        if team_name is not None:
            print(f"Team {team_right_team} is now Team {team_name}")
            team_right_team = team_name

        self._display_manager.set_text("left_team", team_left_team)
        self._display_manager.set_text("right_team", team_right_team)
        self._display_manager.set_text("gender_matchup", gender_matchup)
        self._display_manager.set_text(
            "gender_matchup_counter", str(gender_matchup_count)
        )

    def update_from_network(self) -> None:
        """Update scores and team information from network.

        Fetches latest scores from Adafruit IO and updates display.
        Also updates team names if scores have changed.
        """
        print("Updating data from Adafruit IO")
        self._display_manager.show_connecting(True)

        if self._score_manager.update_scores():
            self.update_team_names()

        self._display_manager.set_text(
            "left_team_score", self._score_manager.left_score
        )
        self._display_manager.set_text(
            "right_team_score", self._score_manager.right_score
        )
        self._display_manager.show_connecting(False)
