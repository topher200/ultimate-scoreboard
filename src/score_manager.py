"""Manages score state."""

from __future__ import annotations

from src.compat import TYPE_CHECKING, Enum

if TYPE_CHECKING:
    from src.nvm_storage import NvmStorage


class ScoreEvent(Enum):
    """Enum representing a score history entry."""

    LEFT = "left"
    RIGHT = "right"
    RESET = "reset"


class ScoreManager:
    def __init__(self, nvm_storage: NvmStorage | None = None):
        """Initialize ScoreManager, restoring scores from NVM if available.

        :param nvm_storage: Optional NvmStorage instance for persisting scores
        """
        self._nvm_storage = nvm_storage
        if nvm_storage is not None:
            from src.nvm_storage import TEAM_LEFT_BYTE, TEAM_RESET_BYTE

            self.left_score, self.right_score = nvm_storage.load_scores()
            self._score_history: list[ScoreEvent] = [
                ScoreEvent.RESET
                if b == TEAM_RESET_BYTE
                else (ScoreEvent.LEFT if b == TEAM_LEFT_BYTE else ScoreEvent.RIGHT)
                for b in nvm_storage.load_history()
            ]
        else:
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
        self.save()

    def save(self) -> None:
        """Persist current scores and undo history to NVM (no-op if no storage configured)."""
        if self._nvm_storage is not None:
            from src.nvm_storage import (
                TEAM_LEFT_BYTE,
                TEAM_RESET_BYTE,
                TEAM_RIGHT_BYTE,
            )

            byte_map = {
                ScoreEvent.LEFT: TEAM_LEFT_BYTE,
                ScoreEvent.RIGHT: TEAM_RIGHT_BYTE,
                ScoreEvent.RESET: TEAM_RESET_BYTE,
            }
            history_bytes = [byte_map[t] for t in self._score_history]
            self._nvm_storage.save(self.left_score, self.right_score, history_bytes)
