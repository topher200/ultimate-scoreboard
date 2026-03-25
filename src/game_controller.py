"""Coordinates game actions and state changes."""

import asyncio

from src.display_manager import DisplayManager
from src.gender_manager import GenderManager
from src.network_manager import NetworkManager
from src.score_manager import ScoreEvent, ScoreManager
from src.timing_indicator import TimingIndicatorManager

NVM_SAVE_DELAY_SECONDS = 1.0


class GameController:
    """Coordinates game actions between managers.

    Handles business logic for button presses and display coordination.
    """

    def __init__(
        self,
        score_manager: ScoreManager,
        display_manager: DisplayManager,
        network_manager: NetworkManager,
        gender_manager: GenderManager,
        timing_indicator_manager: TimingIndicatorManager,
    ):
        """Initialize GameController with manager dependencies.

        :param score_manager: ScoreManager instance for managing scores
        :param display_manager: DisplayManager instance for display updates
        :param network_manager: NetworkManager instance for all network calls
        :param gender_manager: GenderManager instance for keeping track of gender matchups
        :param timing_indicator_manager: TimingIndicatorManager instance for on-screen timing dots
        """
        self._score_manager = score_manager
        self._display_manager = display_manager
        self._network_manager = network_manager
        self._gender_manager = gender_manager
        self._timing_indicator_manager = timing_indicator_manager
        self._pending_save_task: asyncio.Task | None = None

    def _schedule_save(self) -> None:
        """Schedule a debounced NVM save.

        Cancels any pending save and schedules a new one after a short delay,
        so rapid score changes result in only one NVM write.
        """
        if self._pending_save_task is not None:
            self._pending_save_task.cancel()
        self._pending_save_task = asyncio.create_task(self._deferred_save())

    async def _deferred_save(self) -> None:
        """Wait briefly then persist scores to NVM."""
        await asyncio.sleep(NVM_SAVE_DELAY_SECONDS)
        self._schedule_save()

    def initialize_scores(self) -> None:
        """Initialize score display from current score manager state.

        Updates both score displays and the gender matchup display.
        """
        self._display_manager.set_text(
            "left_team_score", self._score_manager.left_score
        )
        self._display_manager.set_text(
            "right_team_score", self._score_manager.right_score
        )
        self._update_gender_matchup_display()

    async def handle_left_score_button(self) -> None:
        """Handle left team score button press.

        Increments the left team score and updates the display.
        """
        print("LEFT button pressed! Incrementing left score...")
        self._score_manager.increment_left_score()
        self._score_manager.record_score_addition(ScoreEvent.LEFT)
        self._display_manager.set_text(
            "left_team_score", self._score_manager.left_score
        )
        print(f"Left score updated: {self._score_manager.left_score}")

        self._update_gender_matchup_display()
        self._refresh_timing_indicator()
        self._schedule_save()

    async def handle_right_score_button(self) -> None:
        """Handle right team score button press.

        Increments the right team score and updates the display.
        """
        print("RIGHT button pressed! Incrementing right score...")
        self._score_manager.increment_right_score()
        self._score_manager.record_score_addition(ScoreEvent.RIGHT)
        self._display_manager.set_text(
            "right_team_score", self._score_manager.right_score
        )
        print(f"Right score updated: {self._score_manager.right_score}")

        self._update_gender_matchup_display()
        self._refresh_timing_indicator()
        self._schedule_save()

    async def handle_undo_button(self) -> None:
        """Handle undo button press.

        Undoes the most recent score addition and updates the display.
        """
        print("DOWN button pressed! Undoing last score...")
        team_to_undo = self._score_manager.undo_last_score()
        if team_to_undo is None:
            print("No score history to undo")
            return

        if team_to_undo == ScoreEvent.RESET:
            self._display_manager.set_text(
                "left_team_score", self._score_manager.left_score
            )
            self._display_manager.set_text(
                "right_team_score", self._score_manager.right_score
            )
            print(
                f"Reset undone: {self._score_manager.left_score}-{self._score_manager.right_score}"
            )
        elif team_to_undo == ScoreEvent.LEFT:
            self._score_manager.decrement_left_score()
            self._display_manager.set_text(
                "left_team_score", self._score_manager.left_score
            )
            print(f"Left score undone: {self._score_manager.left_score}")
        else:  # team_to_undo == ScoreEvent.RIGHT
            self._score_manager.decrement_right_score()
            self._display_manager.set_text(
                "right_team_score", self._score_manager.right_score
            )
            print(f"Right score undone: {self._score_manager.right_score}")

        self._update_gender_matchup_display()
        self._timing_indicator_manager.clear_dots()
        self._display_manager.update_timing_indicator(
            self._timing_indicator_manager.get_dot_count()
        )
        self._schedule_save()

    async def handle_reset_button(self) -> None:
        """Handle reset button press.

        Resets scores to 0-0, clears timing dots, and updates display.
        """
        print("RESET pressed! Resetting scores to 0-0...")
        self._score_manager.reset()
        self._display_manager.set_text(
            "left_team_score", self._score_manager.left_score
        )
        self._display_manager.set_text(
            "right_team_score", self._score_manager.right_score
        )
        self._timing_indicator_manager.clear_dots()
        self._display_manager.update_timing_indicator(
            self._timing_indicator_manager.get_dot_count()
        )
        self._update_gender_matchup_display()
        self._schedule_save()

    async def handle_toggle_gender_button(self) -> None:
        """Handle toggle gender button press.

        Toggles the starting gender between MMP and WMP and recalculates matchup.
        """
        print("UP button pressed! Toggling starting gender...")
        self._gender_manager.toggle_first_point_gender()
        starting_gender = self._gender_manager.get_first_point_gender()
        print(f"Starting gender updated: {starting_gender}")

        self._update_gender_matchup_display()

        # Semi-hack: we're using this button as a shortcut to re-check team
        # names
        await self.update_team_names()

    def set_team_names(self, left_team: str, right_team: str) -> None:
        """Set team names on the display.

        :param left_team: Name for the left team
        :param right_team: Name for the right team
        """
        self._display_manager.set_text("left_team", left_team)
        self._display_manager.set_text("right_team", right_team)

    async def update_team_names(self) -> None:
        """Update team names from network.

        Fetches team names from the network and updates the display.
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

        self.set_team_names(team_left_team, team_right_team)

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

    def _refresh_timing_indicator(self) -> None:
        """Refresh the timing indicator by refilling dots and updating the display."""
        self._timing_indicator_manager.refill_dots()
        self._display_manager.update_timing_indicator(
            self._timing_indicator_manager.get_dot_count()
        )

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
