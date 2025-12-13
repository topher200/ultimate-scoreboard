class GenderManager:
    """Manages first point gender state locally."""

    # Gender constants
    GENDER_WMP = "WMP"
    GENDER_MMP = "MMP"
    DEFAULT_GENDER = GENDER_WMP

    def __init__(self):
        """Initialize GenderManager."""
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
