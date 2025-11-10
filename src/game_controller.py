"""Coordinates game actions and state changes."""

import asyncio
import time

from src.display_manager import DisplayManager
from src.network_manager import NetworkManager
from src.score_manager import ScoreManager


class GameController:
    """Coordinates game actions between managers.

    Handles business logic for button presses, network updates, and display coordination.
    """

    # Network update delay; how often to check for score updates from the internet
    MIN_UPDATE_DELAY = 5.0
    MAX_UPDATE_DELAY = 60.0

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
        self._update_retry_delay = self.MIN_UPDATE_DELAY
        self._last_update_attempt = 0.0

    def _calculate_gender_matchup(self, score_sum: int) -> tuple[str, int]:
        """Calculate gender matchup based on score sum.

        Pattern repeats every 4 points:
        - sum % 4 == 0: WMP2
        - sum % 4 == 1: MMP1
        - sum % 4 == 2: MMP2
        - sum % 4 == 3: WMP1

        :param score_sum: Sum of left and right scores
        :return: Tuple of (matchup_type, counter)
        """
        remainder = score_sum % 4
        if remainder == 0:
            return ("WMP", 2)
        elif remainder == 1:
            return ("MMP", 1)
        elif remainder == 2:
            return ("MMP", 2)
        else:  # remainder == 3
            return ("WMP", 1)

    async def handle_left_score_button(self) -> None:
        """Handle left team score button press.

        Increments the left team score and updates the display.
        """
        print("UP button pressed! Incrementing left score...")
        self._score_manager.increment_left_score()
        self._display_manager.set_text(
            "left_team_score", self._score_manager.left_score
        )
        print(f"Left score updated: {self._score_manager.left_score}")

        score_sum = self._score_manager.left_score + self._score_manager.right_score
        gender_matchup, gender_matchup_count = self._calculate_gender_matchup(score_sum)
        self._display_manager.set_text("gender_matchup", gender_matchup)
        self._display_manager.set_text(
            "gender_matchup_counter", str(gender_matchup_count)
        )

    async def handle_right_score_button(self) -> None:
        """Handle right team score button press.

        Increments the right team score and updates the display.
        """
        print("DOWN button pressed! Incrementing right score...")
        self._score_manager.increment_right_score()
        self._display_manager.set_text(
            "right_team_score", self._score_manager.right_score
        )
        print(f"Right score updated: {self._score_manager.right_score}")

        score_sum = self._score_manager.left_score + self._score_manager.right_score
        gender_matchup, gender_matchup_count = self._calculate_gender_matchup(score_sum)
        self._display_manager.set_text("gender_matchup", gender_matchup)
        self._display_manager.set_text(
            "gender_matchup_counter", str(gender_matchup_count)
        )

    async def update_team_names(self) -> None:
        """Update team names and gender matchup from network.

        Fetches team names from the network and updates the display.
        """
        team_left_team = NetworkManager.DEFAULT_LEFT_TEAM_NAME
        team_right_team = NetworkManager.DEFAULT_RIGHT_TEAM_NAME

        team_name = await self._network_manager.get_left_team_name()
        if team_name is not None:
            print(f"Team {team_left_team} is now Team {team_name}")
            team_left_team = team_name

        await asyncio.sleep(0)

        team_name = await self._network_manager.get_right_team_name()
        if team_name is not None:
            print(f"Team {team_right_team} is now Team {team_name}")
            team_right_team = team_name

        score_sum = self._score_manager.left_score + self._score_manager.right_score
        gender_matchup, gender_matchup_count = self._calculate_gender_matchup(score_sum)

        self._display_manager.set_text("left_team", team_left_team)
        self._display_manager.set_text("right_team", team_right_team)
        self._display_manager.set_text("gender_matchup", gender_matchup)
        self._display_manager.set_text(
            "gender_matchup_counter", str(gender_matchup_count)
        )

    def get_next_update_delay(self) -> float:
        """Get the delay before next network update attempt.

        :return: Delay in seconds
        """
        return self._update_retry_delay

    async def update_from_network(self) -> bool:
        """Update scores and team information from network with exponential backoff.

        Fetches latest scores from Adafruit IO and updates display.
        Also updates team names if scores have changed.

        :return: True if update was successful, False otherwise
        """
        current_time = time.monotonic()
        if current_time - self._last_update_attempt < self._update_retry_delay:
            return False

        self._last_update_attempt = current_time

        try:
            if await self._score_manager.update_scores():
                await asyncio.sleep(0)
                await self.update_team_names()
        except Exception as e:
            print(f"Network update failed: {e}")
            self._update_retry_delay = min(
                self._update_retry_delay * 2, self.MAX_UPDATE_DELAY
            )
            return False
        else:
            self._display_manager.set_text(
                "left_team_score", self._score_manager.left_score
            )
            self._display_manager.set_text(
                "right_team_score", self._score_manager.right_score
            )
            self._update_retry_delay = self.MIN_UPDATE_DELAY
            return True
