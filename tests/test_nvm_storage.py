"""Tests for NvmStorage."""

import pytest

from fakes.fake_nvm import create_fake_nvm
from src.nvm_storage import TEAM_LEFT_BYTE, TEAM_RIGHT_BYTE, NvmStorage


class TestNvmStorage:
    """Test NvmStorage with fake NVM."""

    def test_no_saved_data_on_fresh_nvm(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        assert storage.has_saved_data() is False

    def test_load_returns_zeros_when_no_saved_data(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        assert storage.load_scores() == (0, 0)

    def test_load_returns_empty_history_when_no_saved_data(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        assert storage.load_history() == []

    def test_save_and_load_scores(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save(3, 7, [])
        assert storage.has_saved_data() is True
        assert storage.load_scores() == (3, 7)

    def test_save_and_load_history(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        history = [TEAM_LEFT_BYTE, TEAM_RIGHT_BYTE, TEAM_LEFT_BYTE]
        storage.save(2, 1, history)
        assert storage.load_history() == history

    def test_save_overwrites_previous(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save(1, 2, [TEAM_LEFT_BYTE])
        storage.save(10, 15, [TEAM_RIGHT_BYTE, TEAM_RIGHT_BYTE])
        assert storage.load_scores() == (10, 15)
        assert storage.load_history() == [TEAM_RIGHT_BYTE, TEAM_RIGHT_BYTE]

    def test_clear_removes_saved_data(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save(5, 5, [TEAM_LEFT_BYTE])
        storage.clear()
        assert storage.has_saved_data() is False
        assert storage.load_scores() == (0, 0)
        assert storage.load_history() == []

    def test_persists_across_storage_instances(self):
        """Simulates reboot: same NVM backing, new NvmStorage instance."""
        nvm = create_fake_nvm()
        storage1 = NvmStorage(nvm)
        storage1.save(12, 8, [TEAM_LEFT_BYTE, TEAM_RIGHT_BYTE])

        storage2 = NvmStorage(nvm)
        assert storage2.load_scores() == (12, 8)
        assert storage2.load_history() == [TEAM_LEFT_BYTE, TEAM_RIGHT_BYTE]

    def test_save_zero_scores_with_empty_history(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save(0, 0, [])
        assert storage.has_saved_data() is True
        assert storage.load_scores() == (0, 0)
        assert storage.load_history() == []


class TestScoreManagerWithNvm:
    """Test ScoreManager integration with NvmStorage."""

    def test_restores_scores_on_init(self):
        from src.score_manager import ScoreManager

        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save(5, 3, [])

        score_manager = ScoreManager(nvm_storage=storage)
        assert score_manager.left_score == 5
        assert score_manager.right_score == 3

    def test_restores_undo_history_on_init(self):
        from src.score_manager import ScoreManager, Team

        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save(2, 1, [TEAM_LEFT_BYTE, TEAM_RIGHT_BYTE, TEAM_LEFT_BYTE])

        score_manager = ScoreManager(nvm_storage=storage)
        assert score_manager.undo_last_score() == Team.LEFT
        assert score_manager.undo_last_score() == Team.RIGHT
        assert score_manager.undo_last_score() == Team.LEFT

    def test_save_persists_scores_and_history(self):
        from src.score_manager import ScoreManager, Team

        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        score_manager = ScoreManager(nvm_storage=storage)

        score_manager.increment_left_score()
        score_manager.record_score_addition(Team.LEFT)
        score_manager.increment_left_score()
        score_manager.record_score_addition(Team.LEFT)
        score_manager.increment_right_score()
        score_manager.record_score_addition(Team.RIGHT)
        score_manager.save()

        assert storage.load_scores() == (2, 1)
        assert storage.load_history() == [
            TEAM_LEFT_BYTE,
            TEAM_LEFT_BYTE,
            TEAM_RIGHT_BYTE,
        ]

    def test_no_storage_save_is_noop(self):
        from src.score_manager import ScoreManager

        score_manager = ScoreManager()
        score_manager.increment_left_score()
        score_manager.save()  # Should not raise

    def test_round_trip_simulated_reboot(self):
        """Full round trip: score, save, 'reboot', restore, undo works."""
        from src.score_manager import ScoreManager, Team

        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)

        # First session
        sm1 = ScoreManager(nvm_storage=storage)
        sm1.increment_left_score()
        sm1.record_score_addition(Team.LEFT)
        sm1.increment_right_score()
        sm1.record_score_addition(Team.RIGHT)
        sm1.increment_right_score()
        sm1.record_score_addition(Team.RIGHT)
        sm1.save()

        # Simulated reboot - new ScoreManager, same NVM
        storage2 = NvmStorage(nvm)
        sm2 = ScoreManager(nvm_storage=storage2)
        assert sm2.left_score == 1
        assert sm2.right_score == 2

        # Undo should work after reboot
        assert sm2.undo_last_score() == Team.RIGHT
        assert sm2.right_score == 2  # undo_last_score only pops history
