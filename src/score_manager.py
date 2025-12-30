"""Manages score state."""

from enum import Enum


class Team(Enum):
    """Enum representing the team side."""

    LEFT = "left"
    RIGHT = "right"


class ScoreManager:
    def __init__(self):
        """Initialize ScoreManager."""
        self.left_score: int = 0
        self.right_score: int = 0
        self._score_history: list[Team] = []

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

    def record_score_addition(self, team: Team) -> None:
        """Record a score addition in history.

        :param team: Team.LEFT or Team.RIGHT indicating which team's score was incremented
        """
        self._score_history.append(team)

    def undo_last_score(self) -> Team | None:
        """Undo the most recent score addition.

        :return: Team.LEFT or Team.RIGHT indicating which score to decrement,
            or None if history is empty
        """
        if not self._score_history:
            return None
        return self._score_history.pop()
