"""Tests for GenderManager using fake implementations."""

import pytest

from src.gender_manager import GenderManager


class TestGenderManager:
    """Test GenderManager with fake hardware."""

    def test_initialization(self, gender_manager):
        """Test that GenderManager initializes without errors."""
        assert gender_manager is not None
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP

    async def test_toggle_first_point_gender(self, gender_manager):
        """Test that toggle_first_point_gender toggles between mmp and wmp."""
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP

        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP


WMP = GenderManager.GENDER_WMP
MMP = GenderManager.GENDER_MMP


class TestGetMatchup:
    @pytest.mark.parametrize(
        ("score_sum", "expected"),
        [
            (0, (WMP, 2)),
            (1, (MMP, 1)),
            (2, (MMP, 2)),
            (3, (WMP, 1)),
            (4, (WMP, 2)),
            (20, (WMP, 2)),
            (21, (MMP, 1)),
        ],
    )
    def test_wmp_first_point(self, gender_manager, score_sum, expected):
        assert gender_manager.get_matchup(score_sum) == expected

    @pytest.mark.parametrize(
        ("score_sum", "expected"),
        [(0, (MMP, 2)), (1, (WMP, 1)), (2, (WMP, 2)), (3, (MMP, 1)), (4, (MMP, 2))],
    )
    def test_mmp_first_point(self, gender_manager, score_sum, expected):
        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_matchup(score_sum) == expected
