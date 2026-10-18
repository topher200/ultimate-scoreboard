"""Tests for SettingsStore."""

import pytest

from src.settings_store import (
    DEFAULT_SETTINGS,
    LEFT_TEAM_NAME,
    RIGHT_TEAM_NAME,
    SettingsStore,
)


class TestSettingsStore:
    def test_blank_memory_loads_defaults(self, settings_store):
        assert settings_store.load() == DEFAULT_SETTINGS

    def test_erased_flash_loads_defaults(self):
        store = SettingsStore(bytearray(b"\xff" * 64))

        assert store.load() == DEFAULT_SETTINGS

    def test_save_then_load(self, settings_store):
        settings_store.save({LEFT_TEAM_NAME: "Phoenix", RIGHT_TEAM_NAME: "Tigers"})

        assert settings_store.load() == {
            LEFT_TEAM_NAME: "Phoenix",
            RIGHT_TEAM_NAME: "Tigers",
        }

    def test_missing_and_unknown_keys(self, settings_store):
        settings_store.save({LEFT_TEAM_NAME: "Phoenix", "unknown": "x"})

        assert settings_store.load() == {
            LEFT_TEAM_NAME: "Phoenix",
            RIGHT_TEAM_NAME: DEFAULT_SETTINGS[RIGHT_TEAM_NAME],
        }

    def test_corrupt_json_loads_defaults(self):
        nvm = bytearray(64)
        nvm[0:5] = b"\x00\x03{{{"

        assert SettingsStore(nvm).load() == DEFAULT_SETTINGS

    def test_save_too_large_raises(self):
        store = SettingsStore(bytearray(16))

        with pytest.raises(ValueError):
            store.save({LEFT_TEAM_NAME: "x" * 100})
