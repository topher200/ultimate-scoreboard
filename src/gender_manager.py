from __future__ import annotations

from src.compat import TYPE_CHECKING

if TYPE_CHECKING:
    from src.nvm_storage import NvmStorage


class GenderManager:
    """Manages first point gender state locally."""

    # Gender constants
    GENDER_WMP = "WMP"
    GENDER_MMP = "MMP"
    DEFAULT_GENDER = GENDER_WMP

    def __init__(self, nvm_storage: NvmStorage | None = None):
        """Initialize GenderManager, restoring gender from NVM if available.

        :param nvm_storage: Optional NvmStorage instance for persisting gender setting
        """
        self._nvm_storage = nvm_storage
        if nvm_storage is not None:
            from src.nvm_storage import GENDER_MMP_BYTE

            gender_byte = nvm_storage.load_gender()
            self._first_point_gender: str = (
                self.GENDER_MMP if gender_byte == GENDER_MMP_BYTE else self.GENDER_WMP
            )
        else:
            self._first_point_gender: str = self.DEFAULT_GENDER

    def get_first_point_gender(self) -> str:
        """Get the current first point gender.

        :return: Gender constant (GENDER_WMP or GENDER_MMP)
        """
        return self._first_point_gender

    def toggle_first_point_gender(self) -> None:
        """Toggle the first point gender between MMP and WMP."""
        self._first_point_gender = (
            self.GENDER_MMP
            if self._first_point_gender == self.GENDER_WMP
            else self.GENDER_WMP
        )
        self._save()

    def _save(self) -> None:
        """Persist current gender setting to NVM (no-op if no storage configured)."""
        if self._nvm_storage is not None:
            from src.nvm_storage import GENDER_MMP_BYTE, GENDER_WMP_BYTE

            gender_byte = (
                GENDER_MMP_BYTE
                if self._first_point_gender == self.GENDER_MMP
                else GENDER_WMP_BYTE
            )
            self._nvm_storage.save_gender(gender_byte)
