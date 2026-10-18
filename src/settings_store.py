"""Keeps settings in non-volatile memory across reboots."""

import json

from src.log import WARNING, log

LEFT_TEAM_NAME = "left_team_name"
RIGHT_TEAM_NAME = "right_team_name"

DEFAULT_SETTINGS = {
    LEFT_TEAM_NAME: "AWAY",
    RIGHT_TEAM_NAME: "HOME",
}

# Bytes at the start of the memory that hold the length of the JSON after them
_LENGTH_BYTES = 2


class SettingsStore:
    """Saves settings as JSON in a byte buffer such as microcontroller.nvm."""

    def __init__(self, nvm):
        """Initialize SettingsStore.

        :param nvm: Writable byte buffer that keeps its contents across reboots
        """
        self._nvm = nvm

    def load(self) -> dict:
        """Return the saved settings, with defaults for any that are missing."""
        settings = dict(DEFAULT_SETTINGS)
        length = int.from_bytes(self._nvm[0:_LENGTH_BYTES], "big")
        if length == 0 or length > len(self._nvm) - _LENGTH_BYTES:
            return settings
        try:
            saved = json.loads(
                bytes(self._nvm[_LENGTH_BYTES : _LENGTH_BYTES + length]).decode()
            )
        except (ValueError, UnicodeError) as e:
            log(f"Failed to load settings: {e}", WARNING)
            return settings
        if isinstance(saved, dict):
            for key in DEFAULT_SETTINGS:
                if isinstance(saved.get(key), str):
                    settings[key] = saved[key]
        return settings

    def save(self, settings: dict) -> None:
        """Save settings, replacing what was saved before."""
        data = json.dumps(settings).encode()
        if len(data) > len(self._nvm) - _LENGTH_BYTES:
            raise ValueError("Settings are too large to save")
        self._nvm[0 : _LENGTH_BYTES + len(data)] = (
            len(data).to_bytes(_LENGTH_BYTES, "big") + data
        )
