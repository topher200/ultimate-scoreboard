"""Manages score state."""

from __future__ import annotations

from src.compat import TYPE_CHECKING, Enum

if TYPE_CHECKING:
    from src.nvm_storage import NvmStorage


class Team(Enum):
    """Enum representing the team side."""

    LEFT = "left"
    RIGHT = "right"


class ScoreManager:
    def __init__(self, nvm_storage: NvmStorage | None = None):
        """Initialize ScoreManager, restoring scores from NVM if available.

        :param nvm_storage: Optional NvmStorage instance for persisting scores
        """
        self._nvm_storage = nvm_storage
        if nvm_storage is not None:
            self.left_score, self.right_score = nvm_storage.load_scores()
        else:
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

    def save(self) -> None:
        """Persist current scores to NVM (no-op if no storage configured)."""
        if self._nvm_storage is not None:
            self._nvm_storage.save_scores(self.left_score, self.right_score)
