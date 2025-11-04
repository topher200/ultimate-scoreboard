"""Tests for ScoreManager using fake implementations."""

import unittest

from fakes import FakeMatrixPortal
from score_manager import ScoreManager


class TestScoreManager(unittest.TestCase):
    """Test ScoreManager with fake hardware."""

    def setUp(self):
        """Set up test fixtures."""
        self.fake_portal = FakeMatrixPortal()
        self.left_feed_key = "scores-group.red-team-score-feed"
        self.right_feed_key = "scores-group.blue-team-score-feed"
        self.score_manager = ScoreManager(
            self.fake_portal, self.left_feed_key, self.right_feed_key
        )

    def test_initialization(self):
        """Test that ScoreManager initializes without errors."""
        self.assertIsNotNone(self.score_manager)
        self.assertEqual(self.score_manager.left_score, None)
        self.assertEqual(self.score_manager.right_score, None)

    def test_update_scores_with_none_values_defaults_to_zero(self):
        """Test that None feed values default to 0."""
        self.fake_portal.set_feed_value(self.left_feed_key, None)
        self.fake_portal.set_feed_value(self.right_feed_key, None)

        changed = self.score_manager.update_scores()

        self.assertEqual(self.score_manager.left_score, 0)
        self.assertEqual(self.score_manager.right_score, 0)
        self.assertFalse(changed)

    def test_update_scores_with_initial_values(self):
        """Test updating scores with initial values."""
        self.fake_portal.set_feed_value(self.left_feed_key, 5)
        self.fake_portal.set_feed_value(self.right_feed_key, 3)

        changed = self.score_manager.update_scores()

        self.assertEqual(self.score_manager.left_score, 5)
        self.assertEqual(self.score_manager.right_score, 3)
        self.assertFalse(changed)

    def test_update_scores_detects_left_score_change(self):
        """Test that update_scores returns True when left score changes."""
        self.fake_portal.set_feed_value(self.left_feed_key, 5)
        self.fake_portal.set_feed_value(self.right_feed_key, 3)
        self.score_manager.update_scores()

        self.fake_portal.set_feed_value(self.left_feed_key, 6)
        changed = self.score_manager.update_scores()

        self.assertEqual(self.score_manager.left_score, 6)
        self.assertEqual(self.score_manager.right_score, 3)
        self.assertTrue(changed)

    def test_update_scores_detects_right_score_change(self):
        """Test that update_scores returns True when right score changes."""
        self.fake_portal.set_feed_value(self.left_feed_key, 5)
        self.fake_portal.set_feed_value(self.right_feed_key, 3)
        self.score_manager.update_scores()

        self.fake_portal.set_feed_value(self.right_feed_key, 4)
        changed = self.score_manager.update_scores()

        self.assertEqual(self.score_manager.left_score, 5)
        self.assertEqual(self.score_manager.right_score, 4)
        self.assertTrue(changed)

    def test_update_scores_detects_both_scores_change(self):
        """Test that update_scores returns True when both scores change."""
        self.fake_portal.set_feed_value(self.left_feed_key, 5)
        self.fake_portal.set_feed_value(self.right_feed_key, 3)
        self.score_manager.update_scores()

        self.fake_portal.set_feed_value(self.left_feed_key, 6)
        self.fake_portal.set_feed_value(self.right_feed_key, 4)
        changed = self.score_manager.update_scores()

        self.assertEqual(self.score_manager.left_score, 6)
        self.assertEqual(self.score_manager.right_score, 4)
        self.assertTrue(changed)

    def test_update_scores_no_change_when_scores_same(self):
        """Test that update_scores returns False when scores don't change."""
        self.fake_portal.set_feed_value(self.left_feed_key, 5)
        self.fake_portal.set_feed_value(self.right_feed_key, 3)
        self.score_manager.update_scores()

        changed = self.score_manager.update_scores()

        self.assertEqual(self.score_manager.left_score, 5)
        self.assertEqual(self.score_manager.right_score, 3)
        self.assertFalse(changed)

    def test_update_scores_with_string_values(self):
        """Test that update_scores handles string score values."""
        self.fake_portal.set_feed_value(self.left_feed_key, "10")
        self.fake_portal.set_feed_value(self.right_feed_key, "7")

        changed = self.score_manager.update_scores()

        self.assertEqual(self.score_manager.left_score, "10")
        self.assertEqual(self.score_manager.right_score, "7")
        self.assertFalse(changed)

    def test_update_scores_multiple_updates(self):
        """Test multiple score updates in sequence."""
        self.fake_portal.set_feed_value(self.left_feed_key, 0)
        self.fake_portal.set_feed_value(self.right_feed_key, 0)
        self.score_manager.update_scores()

        self.fake_portal.set_feed_value(self.left_feed_key, 1)
        changed1 = self.score_manager.update_scores()
        self.assertTrue(changed1)

        self.fake_portal.set_feed_value(self.right_feed_key, 1)
        changed2 = self.score_manager.update_scores()
        self.assertTrue(changed2)

        changed3 = self.score_manager.update_scores()
        self.assertFalse(changed3)


if __name__ == "__main__":
    unittest.main()

