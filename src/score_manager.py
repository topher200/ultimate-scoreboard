"""Manages score state."""

from __future__ import annotations

from src.compat import Enum


class ScoreEvent(Enum):
    """Enum representing a score history entry."""

    LEFT = "left"
    RIGHT = "right"
    RESET = "reset"


class ScoreManager:
    def __init__(self):
        """Initialize ScoreManager with scores at 0-0 and no history."""
        self.left_score: int = 0
        self.right_score: int = 0
        self._score_history: list[ScoreEvent] = []

    def increment_left_score(self) -> None:
        """Increment left team score by 1."""
        self.left_score += 1

    def increment_right_score(self) -> None:
        """Increment right team score by 1."""
        self.right_score += 1

    def decrement_left_score(self) -> None:
        """Decrement left team score by 1, preventing it from going below 0."""
        self.left_score = max(0, self.left_score - 1)

    def decrement_right_score(self) -> None:
        """Decrement right team score by 1, preventing it from going below 0."""
        self.right_score = max(0, self.right_score - 1)

    def record_score_addition(self, team: ScoreEvent) -> None:
        """Record a score addition in history.

        :param team: ScoreEvent.LEFT or ScoreEvent.RIGHT indicating which team scored
        """
        self._score_history.append(team)

    def undo_last_score(self) -> ScoreEvent | None:
        """Undo the most recent score addition or reset.

        :return: ScoreEvent.LEFT, ScoreEvent.RIGHT, or ScoreEvent.RESET indicating what was undone,
            or None if history is empty
        """
        if not self._score_history:
            return None
        entry = self._score_history.pop()
        if entry == ScoreEvent.RESET:
            self._reconstruct_scores()
        return entry

    def _reconstruct_scores(self) -> None:
        """Reconstruct scores from history after undoing a reset.

        Scans backward from the end of history to the previous RESET
        (or start), counting LEFT and RIGHT entries.
        """
        left = 0
        right = 0
        for entry in reversed(self._score_history):
            if entry == ScoreEvent.RESET:
                break
            elif entry == ScoreEvent.LEFT:
                left += 1
            elif entry == ScoreEvent.RIGHT:
                right += 1
        self.left_score = left
        self.right_score = right

    def reset(self) -> None:
        """Reset scores to 0-0 and record in history for undo support."""
        self._score_history.append(ScoreEvent.RESET)
        self.left_score = 0
        self.right_score = 0
