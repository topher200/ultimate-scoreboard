"""Non-volatile memory storage for persisting scores across reboots."""


class NvmStorage:
    """Wraps a byte-array-like NVM object to save/load scores."""

    MAGIC = 0xAB
    OFFSET_MAGIC = 0
    OFFSET_LEFT = 1
    OFFSET_RIGHT = 2

    def __init__(self, nvm):
        """Initialize NvmStorage.

        :param nvm: A byte-array-like object (microcontroller.nvm on hardware,
            bytearray in tests/simulator)
        """
        self._nvm = nvm

    def has_saved_scores(self) -> bool:
        """Check if NVM contains valid saved scores.

        :return: True if the magic marker is present
        """
        return self._nvm[self.OFFSET_MAGIC] == self.MAGIC

    def load_scores(self) -> tuple[int, int]:
        """Load saved scores from NVM.

        :return: Tuple of (left_score, right_score), or (0, 0) if no saved data
        """
        if not self.has_saved_scores():
            return (0, 0)
        return (self._nvm[self.OFFSET_LEFT], self._nvm[self.OFFSET_RIGHT])

    def save_scores(self, left: int, right: int) -> None:
        """Save scores to NVM in a single write to minimize flash wear.

        :param left: Left team score (0–255)
        :param right: Right team score (0–255)
        """
        self._nvm[0:3] = bytes([self.MAGIC, left, right])

    def clear(self) -> None:
        """Clear saved scores from NVM."""
        self._nvm[0:3] = bytes([0x00, 0x00, 0x00])
