"""Manages score state."""


class ScoreManager:
    def __init__(self):
        """Initialize ScoreManager."""
        self.left_score: int = 0
        self.right_score: int = 0

    def increment_left_score(self) -> None:
        """Increment left team score by 1."""
        self.left_score += 1

    def increment_right_score(self) -> None:
        """Increment right team score by 1."""
        self.right_score += 1
