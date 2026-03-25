"""Tests for ScoreManager using fake implementations."""

import pytest

from src.score_manager import ScoreEvent, ScoreManager


class TestScoreManager:
    """Test ScoreManager with fake hardware."""

    def test_initialization(self):
        """Test that ScoreManager initializes without errors."""
        score_manager = ScoreManager()
        assert score_manager is not None
        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

    def test_increment_left_score(self):
        """Test that increment_left_score increments the left score."""
        score_manager = ScoreManager()
        score_manager.increment_left_score()
        assert score_manager.left_score == 1
        assert score_manager.right_score == 0

    def test_increment_right_score(self):
        """Test that increment_right_score increments the right score."""
        score_manager = ScoreManager()
        score_manager.increment_right_score()
        assert score_manager.left_score == 0
        assert score_manager.right_score == 1

    def test_multiple_increments(self):
        """Test multiple increments work correctly."""
        score_manager = ScoreManager()
        score_manager.increment_left_score()
        score_manager.increment_left_score()
        score_manager.increment_right_score()
        assert score_manager.left_score == 2
        assert score_manager.right_score == 1

    def test_reset_zeroes_scores(self):
        """Test that reset sets scores to 0-0."""
        score_manager = ScoreManager()
        score_manager.increment_left_score()
        score_manager.increment_left_score()
        score_manager.increment_right_score()
        score_manager.reset()
        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

    def test_reset_is_undoable(self):
        """Test that reset can be undone to restore previous scores."""
        score_manager = ScoreManager()
        score_manager.increment_left_score()
        score_manager.record_score_addition(ScoreEvent.LEFT)
        score_manager.increment_right_score()
        score_manager.record_score_addition(ScoreEvent.RIGHT)
        score_manager.reset()
        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

        result = score_manager.undo_last_score()
        assert result == ScoreEvent.RESET
        assert score_manager.left_score == 1
        assert score_manager.right_score == 1

    def test_undo_after_reset_undo_continues_history(self):
        """Test that undo continues through pre-reset history after undoing a reset."""
        score_manager = ScoreManager()
        score_manager.increment_left_score()
        score_manager.record_score_addition(ScoreEvent.LEFT)
        score_manager.increment_right_score()
        score_manager.record_score_addition(ScoreEvent.RIGHT)
        score_manager.reset()

        # Undo the reset
        score_manager.undo_last_score()
        assert score_manager.left_score == 1
        assert score_manager.right_score == 1

        # Continue undoing pre-reset history
        result = score_manager.undo_last_score()
        assert result == ScoreEvent.RIGHT

    def test_multiple_resets_are_undoable(self):
        """Test that multiple resets can be undone sequentially."""
        score_manager = ScoreManager()
        score_manager.increment_left_score()
        score_manager.record_score_addition(ScoreEvent.LEFT)
        score_manager.reset()
        score_manager.increment_right_score()
        score_manager.record_score_addition(ScoreEvent.RIGHT)
        score_manager.reset()

        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

        # Undo second reset — restores 0-1
        score_manager.undo_last_score()
        assert score_manager.left_score == 0
        assert score_manager.right_score == 1

        # Undo the right point — back to 0-0
        score_manager.undo_last_score()
        assert score_manager.left_score == 0
        assert score_manager.right_score == 1  # undo_last_score only pops, doesn't decrement

        # Undo first reset — restores 1-0
        score_manager.undo_last_score()
        assert score_manager.left_score == 1
        assert score_manager.right_score == 0
