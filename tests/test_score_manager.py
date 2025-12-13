"""Tests for ScoreManager using fake implementations."""

import pytest

from src.score_manager import ScoreManager


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
