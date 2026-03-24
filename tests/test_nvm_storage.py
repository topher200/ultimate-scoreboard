"""Tests for NvmStorage."""

import pytest

from fakes.fake_nvm import create_fake_nvm
from src.nvm_storage import NvmStorage


class TestNvmStorage:
    """Test NvmStorage with fake NVM."""

    def test_no_saved_scores_on_fresh_nvm(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        assert storage.has_saved_scores() is False

    def test_load_returns_zeros_when_no_saved_data(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        assert storage.load_scores() == (0, 0)

    def test_save_and_load_scores(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save_scores(3, 7)
        assert storage.has_saved_scores() is True
        assert storage.load_scores() == (3, 7)

    def test_save_overwrites_previous(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save_scores(1, 2)
        storage.save_scores(10, 15)
        assert storage.load_scores() == (10, 15)

    def test_clear_removes_saved_scores(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save_scores(5, 5)
        storage.clear()
        assert storage.has_saved_scores() is False
        assert storage.load_scores() == (0, 0)

    def test_persists_across_storage_instances(self):
        """Simulates reboot: same NVM backing, new NvmStorage instance."""
        nvm = create_fake_nvm()
        storage1 = NvmStorage(nvm)
        storage1.save_scores(12, 8)

        storage2 = NvmStorage(nvm)
        assert storage2.load_scores() == (12, 8)

    def test_save_zero_scores(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save_scores(0, 0)
        assert storage.has_saved_scores() is True
        assert storage.load_scores() == (0, 0)


class TestScoreManagerWithNvm:
    """Test ScoreManager integration with NvmStorage."""

    def test_restores_scores_on_init(self):
        from src.score_manager import ScoreManager

        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save_scores(5, 3)

        score_manager = ScoreManager(nvm_storage=storage)
        assert score_manager.left_score == 5
        assert score_manager.right_score == 3

    def test_save_persists_current_scores(self):
        from src.score_manager import ScoreManager

        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        score_manager = ScoreManager(nvm_storage=storage)

        score_manager.increment_left_score()
        score_manager.increment_left_score()
        score_manager.increment_right_score()
        score_manager.save()

        assert storage.load_scores() == (2, 1)

    def test_no_storage_save_is_noop(self):
        from src.score_manager import ScoreManager

        score_manager = ScoreManager()
        score_manager.increment_left_score()
        score_manager.save()  # Should not raise

    def test_round_trip_simulated_reboot(self):
        """Full round trip: score, save, 'reboot', restore."""
        from src.score_manager import ScoreManager

        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)

        # First session
        sm1 = ScoreManager(nvm_storage=storage)
        sm1.increment_left_score()
        sm1.increment_right_score()
        sm1.increment_right_score()
        sm1.save()

        # Simulated reboot - new ScoreManager, same NVM
        storage2 = NvmStorage(nvm)
        sm2 = ScoreManager(nvm_storage=storage2)
        assert sm2.left_score == 1
        assert sm2.right_score == 2
