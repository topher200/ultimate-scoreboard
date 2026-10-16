from __future__ import annotations


class GenderManager:
    """Manages first point gender state and the per-point gender matchup."""

    # Gender constants
    GENDER_WMP = "WMP"
    GENDER_MMP = "MMP"
    DEFAULT_GENDER = GENDER_WMP

    # ABBA cycle with a WMP first point: WMP2, MMP1, MMP2, WMP1
    _MATCHUP_CYCLE = (
        (GENDER_WMP, 2),
        (GENDER_MMP, 1),
        (GENDER_MMP, 2),
        (GENDER_WMP, 1),
    )

    def __init__(self):
        """Initialize GenderManager with the default first point gender."""
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

    def get_matchup(self, score_sum: int) -> tuple[str, int]:
        """Get the gender matchup for the next point.

        An MMP first point shifts the cycle by two: MMP2, WMP1, WMP2, MMP1.

        :param score_sum: Sum of left and right scores
        :return: Tuple of (gender, count)
        """
        offset = 0 if self._first_point_gender == self.GENDER_WMP else 2
        return self._MATCHUP_CYCLE[(score_sum + offset) % 4]
