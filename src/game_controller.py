"""Coordinates game actions and state changes."""

import asyncio
import time

from src.display_manager import DisplayManager
from src.gender_manager import GenderManager
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
        gender_manager: GenderManager,
    ):
        """Initialize GameController with manager dependencies.

        :param display_manager: DisplayManager instance for display updates
        :param network_manager: NetworkManager instance for all network calls
        :param score_manager: ScoreManager instance for managing scores
        :param gender_manager: GenderManager instance for keeping track of gender matchups
        """
        self._score_manager = score_manager
        self._display_manager = display_manager
        self._network_manager = network_manager
        self._gender_manager = gender_manager
        self._update_retry_delay = self.MIN_UPDATE_DELAY
        self._last_update_attempt = 0.0

    def _calculate_gender_matchup(
        self, score_sum: int, starting_gender: str
    ) -> tuple[str, int]:
        """Calculate gender matchup based on score sum and starting gender.

        Pattern always cycles: WMP2 → MMP1 → MMP2 → WMP1 → WMP2 → ...
        - If starting_gender=GENDER_WMP: SUM=0→WMP2, SUM=1→MMP1, SUM=2→MMP2, SUM=3→WMP1
        - If starting_gender=GENDER_MMP: SUM=0→MMP2, SUM=1→WMP1, SUM=2→WMP2, SUM=3→MMP1

        :param score_sum: Sum of left and right scores
        :param starting_gender: Starting gender (GenderManager.GENDER_WMP or
            GenderManager.GENDER_MMP)
        :return: Tuple of (matchup_type, counter)
        """
        # Base pattern: WMP2 (0), MMP1 (1), MMP2 (2), WMP1 (3)
        # Offset: 0 for WMP2 start, 2 for MMP2 start
        offset = 0 if starting_gender == GenderManager.GENDER_WMP else 2
        position = (score_sum + offset) % 4

        if position == 0:
            return ("WMP", 2)
        elif position == 1:
            return ("MMP", 1)
        elif position == 2:
            return ("MMP", 2)
        else:  # position == 3
            return ("WMP", 1)

    def _update_gender_matchup_display(self) -> None:
        """Update the gender matchup display based on current scores and starting gender."""
        score_sum = self._score_manager.left_score + self._score_manager.right_score
        starting_gender = self._gender_manager.get_first_point_gender()
        gender_matchup, gender_matchup_count = self._calculate_gender_matchup(
            score_sum, starting_gender
        )
        self._display_manager.set_text("gender_matchup", gender_matchup)
        self._display_manager.set_text(
            "gender_matchup_counter", str(gender_matchup_count)
        )

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

        self._update_gender_matchup_display()

    async def handle_toggle_gender_button(self) -> None:
        """Handle toggle gender button press.

        Toggles the starting gender between MMP and WMP and recalculates matchup.
        """
        print("UP button pressed! Toggling starting gender...")
        self._gender_manager.toggle_first_point_gender()
        starting_gender = self._gender_manager.get_first_point_gender()
        print(f"Starting gender updated: {starting_gender}")

        self._update_gender_matchup_display()

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

        self._update_gender_matchup_display()

    async def update_team_names_and_gender(self) -> None:
        """Update team names and gender matchup from network.

        Fetches team names and gender feed from the network and updates the display.
        """
        team_left_team = NetworkManager.DEFAULT_LEFT_TEAM_NAME
        team_right_team = NetworkManager.DEFAULT_RIGHT_TEAM_NAME

        await asyncio.sleep(0)
        team_name = await self._network_manager.get_left_team_name()
        if team_name is not None:
            print(f"Team {team_left_team} is now Team {team_name}")
            team_left_team = team_name

        await asyncio.sleep(0)
        team_name = await self._network_manager.get_right_team_name()
        if team_name is not None:
            print(f"Team {team_right_team} is now Team {team_name}")
            team_right_team = team_name

        self._display_manager.set_text("left_team", team_left_team)
        self._display_manager.set_text("right_team", team_right_team)

        await asyncio.sleep(0)
        await self._gender_manager.update_gender_from_network()
        self._update_gender_matchup_display()

    def get_next_update_delay(self) -> float:
        """Get the delay before next network update attempt.

        :return: Delay in seconds
        """
        return self._update_retry_delay

    def reset_update_timing(self) -> None:
        """Reset update timing to allow immediate update attempts.

        Primarily intended for testing purposes to bypass timing restrictions.
        """
        self._last_update_attempt = 0.0

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
            score_changed = await self._score_manager.update_scores()
        except Exception as e:
            print(f"Network update failed: {e}")
            self._update_retry_delay = min(
                self._update_retry_delay * 2, self.MAX_UPDATE_DELAY
            )
            return False

        self._display_manager.set_text(
            "left_team_score", self._score_manager.left_score
        )
        self._display_manager.set_text(
            "right_team_score", self._score_manager.right_score
        )
        self._update_gender_matchup_display()

        if score_changed:
            await self.update_team_names_and_gender()

        self._update_retry_delay = self.MIN_UPDATE_DELAY
        return True
