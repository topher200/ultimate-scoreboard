"""Tests for GenderManager using fake implementations."""

import pytest

from fakes.fake_nvm import create_fake_nvm
from src.gender_manager import GenderManager
from src.nvm_storage import GENDER_MMP_BYTE, GENDER_WMP_BYTE, NvmStorage


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


class TestGenderManagerWithNvm:
    """Test GenderManager integration with NvmStorage."""

    def test_defaults_to_wmp_on_fresh_nvm(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        gm = GenderManager(nvm_storage=storage)
        assert gm.get_first_point_gender() == GenderManager.GENDER_WMP

    def test_restores_gender_from_nvm(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        storage.save_gender(GENDER_MMP_BYTE)

        gm = GenderManager(nvm_storage=storage)
        assert gm.get_first_point_gender() == GenderManager.GENDER_MMP

    def test_toggle_persists_to_nvm(self):
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)
        gm = GenderManager(nvm_storage=storage)

        gm.toggle_first_point_gender()
        assert storage.load_gender() == GENDER_MMP_BYTE

        gm.toggle_first_point_gender()
        assert storage.load_gender() == GENDER_WMP_BYTE

    def test_round_trip_simulated_reboot(self):
        """Toggle gender, 'reboot', verify it persists."""
        nvm = create_fake_nvm()
        storage = NvmStorage(nvm)

        gm1 = GenderManager(nvm_storage=storage)
        gm1.toggle_first_point_gender()
        assert gm1.get_first_point_gender() == GenderManager.GENDER_MMP

        # Simulated reboot
        storage2 = NvmStorage(nvm)
        gm2 = GenderManager(nvm_storage=storage2)
        assert gm2.get_first_point_gender() == GenderManager.GENDER_MMP

    def test_no_storage_toggle_is_noop_save(self):
        gm = GenderManager()
        gm.toggle_first_point_gender()  # Should not raise
        assert gm.get_first_point_gender() == GenderManager.GENDER_MMP
