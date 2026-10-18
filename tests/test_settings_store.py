"""Tests for SettingsStore."""

import pytest

from src.settings_store import (
    DEFAULT_SETTINGS,
    LEFT_TEAM_NAME,
    MARCH_WMP_FRAME,
    RIGHT_TEAM_NAME,
    SHOW_WMP_FRAME,
    SettingsStore,
)


class TestSettingsStore:
    def test_blank_memory_loads_defaults(self, settings_store):
        assert settings_store.load() == DEFAULT_SETTINGS

    def test_erased_flash_loads_defaults(self):
        store = SettingsStore(bytearray(b"\xff" * 64))

        assert store.load() == DEFAULT_SETTINGS

    def test_save_then_load(self, settings_store):
        saved = {
            LEFT_TEAM_NAME: "Phoenix",
            RIGHT_TEAM_NAME: "Tigers",
            SHOW_WMP_FRAME: False,
            MARCH_WMP_FRAME: False,
        }
        settings_store.save(saved)

        assert settings_store.load() == saved

    def test_missing_and_unknown_keys(self, settings_store):
        settings_store.save({LEFT_TEAM_NAME: "Phoenix", "unknown": "x"})

        assert settings_store.load() == {
            **DEFAULT_SETTINGS,
            LEFT_TEAM_NAME: "Phoenix",
        }

    def test_values_of_the_wrong_type_load_defaults(self, settings_store):
        settings_store.save({LEFT_TEAM_NAME: 5, SHOW_WMP_FRAME: "no"})

        assert settings_store.load() == DEFAULT_SETTINGS

    def test_corrupt_json_loads_defaults(self):
        nvm = bytearray(64)
        nvm[0:5] = b"\x00\x03{{{"

        assert SettingsStore(nvm).load() == DEFAULT_SETTINGS

    def test_save_too_large_raises(self):
        store = SettingsStore(bytearray(16))

        with pytest.raises(ValueError):
            store.save({LEFT_TEAM_NAME: "x" * 100})
