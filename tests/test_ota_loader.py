"""Tests for the OTA slot loader."""

import sys
from unittest.mock import Mock

import pytest

import ota_loader


@pytest.fixture
def root(tmp_path):
    return f"{tmp_path}/"


@pytest.fixture(autouse=True)
def restore_sys_path():
    saved = list(sys.path)
    yield
    sys.path[:] = saved


def crash():
    raise RuntimeError("boom")


class TestSlots:
    def test_no_state_runs_the_root_app(self, root):
        assert ota_loader.app_path(root) is None
        assert ota_loader.inactive_slot(root) == "a"

    def test_trial_runs_the_new_slot(self, root):
        ota_loader.start_trial(root, "a", "1.1.0")

        assert ota_loader.app_path(root) == f"{root}slots/a"
        assert ota_loader.inactive_slot(root) == "b"
        assert ota_loader.in_trial(root)

    def test_damaged_state_runs_the_root_app(self, root):
        with open(root + ota_loader.STATE_FILE, "w") as f:
            f.write("{not json")

        assert ota_loader.app_path(root) is None

    def test_state_survives_a_write_cut_off_before_the_rename(self, root):
        ota_loader.start_trial(root, "a", "1.1.0")
        ota_loader.remove_tree(root + ota_loader.STATE_FILE)
        with open(root + ota_loader.STATE_TEMP_FILE, "w") as f:
            f.write('{"active": "b"}')

        assert ota_loader.app_path(root) == f"{root}slots/b"


class TestRunApp:
    def test_runs_the_active_slot(self, root):
        ota_loader.start_trial(root, "a", "1.1.0")
        start = Mock()

        ota_loader.run_app(root, start, Mock())

        start.assert_called_once()
        assert sys.path[0] == f"{root}slots/a"

    def test_crash_in_trial_rolls_back_and_resets(self, root):
        ota_loader.start_trial(root, "a", "1.1.0")
        ota_loader.mark_healthy(root)
        ota_loader.start_trial(root, "b", "1.2.0")
        reset = Mock()

        ota_loader.run_app(root, crash, reset)

        reset.assert_called_once()
        assert ota_loader.app_path(root) == f"{root}slots/a"
        assert not ota_loader.in_trial(root)
        assert ota_loader.rolled_back_version(root) == "1.2.0"

    def test_crash_of_first_slot_rolls_back_to_the_root_app(self, root):
        ota_loader.start_trial(root, "a", "1.1.0")

        ota_loader.run_app(root, crash, Mock())

        assert ota_loader.app_path(root) is None

    def test_crash_after_check_in_raises_without_reset(self, root):
        ota_loader.start_trial(root, "a", "1.1.0")
        ota_loader.mark_healthy(root)
        reset = Mock()

        with pytest.raises(RuntimeError):
            ota_loader.run_app(root, crash, reset)

        reset.assert_not_called()
        assert ota_loader.app_path(root) == f"{root}slots/a"


class TestFiles:
    def test_make_dirs_and_remove_tree(self, root):
        ota_loader.make_dirs(root + "x/y/z")
        with open(root + "x/y/z/file.txt", "w") as f:
            f.write("data")

        ota_loader.remove_tree(root + "x")

        with pytest.raises(OSError):
            open(root + "x/y/z/file.txt")
