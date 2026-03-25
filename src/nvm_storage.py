"""Non-volatile memory storage for persisting scores across reboots.

NVM layout:
    [0]        magic marker (0xAB) — indicates valid saved data
    [1]        left score (0–255)
    [2]        right score (0–255)
    [3]        gender setting (0x00=WMP, 0x01=MMP)
    [4]        history length
    [5..5+len] history entries (0x00=LEFT, 0x01=RIGHT, 0x02=RESET)
"""

TEAM_LEFT_BYTE = 0x00
TEAM_RIGHT_BYTE = 0x01
TEAM_RESET_BYTE = 0x02

MAX_HISTORY_LENGTH = 150

GENDER_WMP_BYTE = 0x00
GENDER_MMP_BYTE = 0x01


class NvmStorage:
    """Wraps a byte-array-like NVM object to save/load scores and undo history."""

    MAGIC = 0xAB
    OFFSET_MAGIC = 0
    OFFSET_LEFT = 1
    OFFSET_RIGHT = 2
    OFFSET_GENDER = 3
    OFFSET_HISTORY_LEN = 4
    OFFSET_HISTORY_START = 5

    def __init__(self, nvm):
        """Initialize NvmStorage.

        :param nvm: A byte-array-like object (microcontroller.nvm on hardware,
            bytearray in tests/simulator)
        """
        self._nvm = nvm

    def has_saved_data(self) -> bool:
        """Check if NVM contains valid saved data.

        :return: True if the magic marker is present
        """
        return self._nvm[self.OFFSET_MAGIC] == self.MAGIC

    def load_scores(self) -> tuple[int, int]:
        """Load saved scores from NVM.

        :return: Tuple of (left_score, right_score), or (0, 0) if no saved data
        """
        if not self.has_saved_data():
            return (0, 0)
        return (self._nvm[self.OFFSET_LEFT], self._nvm[self.OFFSET_RIGHT])

    def load_history(self) -> list[int]:
        """Load undo history from NVM.

        :return: List of event bytes (TEAM_LEFT_BYTE, TEAM_RIGHT_BYTE, or TEAM_RESET_BYTE),
            or [] if no saved data
        """
        if not self.has_saved_data():
            return []
        length = self._nvm[self.OFFSET_HISTORY_LEN]
        start = self.OFFSET_HISTORY_START
        return list(self._nvm[start : start + length])

    def load_gender(self) -> int:
        """Load saved gender setting from NVM.

        :return: Gender byte (GENDER_WMP_BYTE or GENDER_MMP_BYTE), defaults to WMP if no saved data
        """
        if not self.has_saved_data():
            return GENDER_WMP_BYTE
        gender_byte = self._nvm[self.OFFSET_GENDER]
        if gender_byte not in {GENDER_WMP_BYTE, GENDER_MMP_BYTE}:
            return GENDER_WMP_BYTE
        return gender_byte

    def save(self, left: int, right: int, history: list[int]) -> None:
        """Save scores and undo history to NVM in a single write.

        Preserves the existing gender setting.

        :param left: Left team score (0–255)
        :param right: Right team score (0–255)
        :param history: List of event bytes (TEAM_LEFT_BYTE, TEAM_RIGHT_BYTE, or TEAM_RESET_BYTE)
        """
        gender = self.load_gender()
        history = history[-MAX_HISTORY_LENGTH:]
        length = len(history)
        data = bytes([self.MAGIC, left, right, gender, length]) + bytes(history)
        self._nvm[0 : self.OFFSET_HISTORY_START + length] = data

    def save_gender(self, gender_byte: int) -> None:
        """Save gender setting to NVM.

        :param gender_byte: GENDER_WMP_BYTE or GENDER_MMP_BYTE
        """
        self._nvm[self.OFFSET_MAGIC] = self.MAGIC
        self._nvm[self.OFFSET_GENDER] = gender_byte

    def clear(self) -> None:
        """Clear all saved data from NVM."""
        self._nvm[0 : self.OFFSET_HISTORY_START] = bytes(
            [0x00] * self.OFFSET_HISTORY_START
        )
