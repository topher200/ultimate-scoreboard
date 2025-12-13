"""Tests for GenderManager using fake implementations."""

import pytest

from src.gender_manager import GenderManager


class TestGenderManager:
    """Test GenderManager with fake hardware."""

    def test_initialization(self, gender_manager):
        """Test that GenderManager initializes without errors."""
        assert gender_manager is not None
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP

    @pytest.mark.asyncio
    async def test_toggle_first_point_gender(self, gender_manager):
        """Test that toggle_first_point_gender toggles between mmp and wmp."""
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP

        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP
