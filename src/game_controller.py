"""Coordinates game actions and state changes."""

from src.display_manager import DisplayManager
from src.gender_manager import GenderManager
from src.network_manager import NetworkManager
from src.score_manager import ScoreEvent, ScoreManager
from src.timing_indicator import TimingIndicatorManager


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

    def initialize_scores(self) -> None:
        """Initialize score display from current score manager state.

        Updates both score displays and the gender matchup display.
        """
        self._redraw_scores()
        self._update_gender_matchup_display()

    async def handle_left_score_button(self) -> None:
        """Add a point for the left team."""
        print("LEFT button pressed!")
        self._add_point(ScoreEvent.LEFT)

    async def handle_right_score_button(self) -> None:
        """Add a point for the right team."""
        print("RIGHT button pressed!")
        self._add_point(ScoreEvent.RIGHT)

    async def handle_undo_button(self) -> None:
        """Undo the most recent point or reset and update the display."""
        print("UNDO pressed! Undoing last score...")
        entry = self._score_manager.undo_last_score()
        if entry is None:
            print("No score history to undo")
            return

        if entry == ScoreEvent.LEFT:
            self._score_manager.decrement_left_score()
        elif entry == ScoreEvent.RIGHT:
            self._score_manager.decrement_right_score()
        self._redraw_scores()
        self._print_score("Undone")
        self._update_gender_matchup_display()
        self._clear_timing_indicator()

    async def handle_reset_button(self) -> None:
        """Reset scores to 0-0, clear the timing indicator, and update the display."""
        print("RESET pressed! Resetting scores to 0-0...")
        self._score_manager.reset()
        self._redraw_scores()
        self._clear_timing_indicator()
        self._update_gender_matchup_display()

    async def handle_toggle_gender_button(self) -> None:
        """Handle toggle gender button press.

        Toggles the starting gender between MMP and WMP and recalculates matchup.
        """
        print("TOGGLE GENDER pressed! Toggling starting gender...")
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
        left_team = await self._network_manager.get_left_team_name()
        right_team = await self._network_manager.get_right_team_name()
        print(f"Team names: {left_team} vs {right_team}")
        self.set_team_names(left_team, right_team)

    def _add_point(self, team: ScoreEvent) -> None:
        if team == ScoreEvent.LEFT:
            self._score_manager.increment_left_score()
        else:
            self._score_manager.increment_right_score()
        self._score_manager.record_score_addition(team)
        self._redraw_scores()
        self._print_score("Score")
        self._update_gender_matchup_display()
        self._refresh_timing_indicator()

    def _print_score(self, prefix: str) -> None:
        left = self._score_manager.left_score
        right = self._score_manager.right_score
        print(f"{prefix}: {left}-{right}")

    def _redraw_scores(self) -> None:
        self._display_manager.set_text(
            "left_team_score", self._score_manager.left_score
        )
        self._display_manager.set_text(
            "right_team_score", self._score_manager.right_score
        )

    def _refresh_timing_indicator(self) -> None:
        """Refill the timing indicator and update the display."""
        self._timing_indicator_manager.refill_dots()
        self._display_manager.update_timing_indicator(
            self._timing_indicator_manager.get_dot_count()
        )

    def _clear_timing_indicator(self) -> None:
        """Empty the timing indicator and update the display."""
        self._timing_indicator_manager.clear_dots()
        self._display_manager.update_timing_indicator(
            self._timing_indicator_manager.get_dot_count()
        )

    def _update_gender_matchup_display(self) -> None:
        """Update the gender matchup display based on current scores and starting gender."""
        score_sum = self._score_manager.left_score + self._score_manager.right_score
        gender, count = self._gender_manager.get_matchup(score_sum)
        self._display_manager.set_text("gender_matchup", gender)
        self._display_manager.set_text("gender_matchup_counter", str(count))
