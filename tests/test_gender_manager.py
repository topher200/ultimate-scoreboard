"""Tests for GenderManager using fake implementations."""

import time
from unittest.mock import AsyncMock, patch

import pytest

from src.gender_manager import GenderManager
from src.network_manager import NetworkManager


class TestGenderManager:
    """Test GenderManager with fake hardware."""

    def test_initialization(self, gender_manager):
        """Test that GenderManager initializes without errors."""
        assert gender_manager is not None
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP

    @pytest.mark.asyncio
    async def test_update_gender_from_network_with_initial_value(
        self, gender_manager, fake_matrix_portal
    ):
        """Test updating gender with initial value from network."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "mmp")

        changed = await gender_manager.update_gender_from_network()

        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP
        assert changed

    @pytest.mark.asyncio
    async def test_update_gender_from_network_detects_change(
        self, gender_manager, fake_matrix_portal
    ):
        """Test that update_gender_from_network returns True when gender changes."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "wmp")
        await gender_manager.update_gender_from_network()

        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "mmp")
        changed = await gender_manager.update_gender_from_network()

        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP
        assert changed

    @pytest.mark.asyncio
    async def test_update_gender_from_network_no_change_when_same(
        self, gender_manager, fake_matrix_portal
    ):
        """Test that update_gender_from_network returns False when gender doesn't change."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "wmp")
        await gender_manager.update_gender_from_network()

        changed = await gender_manager.update_gender_from_network()

        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP
        assert not changed

    @pytest.mark.asyncio
    async def test_toggle_first_point_gender(self, gender_manager):
        """Test that toggle_first_point_gender toggles between mmp and wmp."""
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP

        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_WMP

    @pytest.mark.asyncio
    async def test_toggle_sets_pending_sync_flag(self, gender_manager):
        """Test that toggling gender sets the pending sync flag."""
        assert not gender_manager.has_pending_changes()

        gender_manager.toggle_first_point_gender()
        assert gender_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_successful_sync_clears_pending_flag(self, gender_manager):
        """Test that successful sync clears the pending sync flag."""
        gender_manager.toggle_first_point_gender()
        assert gender_manager.has_pending_changes()

        success = await gender_manager.try_sync_gender()
        assert success
        assert not gender_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_failed_sync_keeps_pending_flag(
        self, gender_manager, network_manager
    ):
        """Test that failed sync keeps the pending sync flag set."""
        gender_manager.toggle_first_point_gender()

        with patch.object(
            network_manager,
            "set_first_point_gender",
            side_effect=Exception("Network error"),
        ):
            success = await gender_manager.try_sync_gender()
            assert not success
            assert gender_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_update_gender_skips_network_when_pending_sync(
        self, gender_manager, fake_matrix_portal, network_manager
    ):
        """Test that update_gender_from_network skips network fetch when pending."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "mmp")

        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP
        assert gender_manager.has_pending_changes()

        with patch.object(
            network_manager,
            "set_first_point_gender",
            side_effect=Exception("Network error"),
        ):
            changed = await gender_manager.update_gender_from_network()
            assert not changed
            assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

    @pytest.mark.asyncio
    async def test_update_gender_fetches_when_no_pending_sync(
        self, gender_manager, fake_matrix_portal
    ):
        """Test that update_gender_from_network fetches from network when no pending changes."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "mmp")

        assert not gender_manager.has_pending_changes()
        changed = await gender_manager.update_gender_from_network()

        assert changed
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self, gender_manager, network_manager):
        """Test that retry delay follows exponential backoff pattern."""
        gender_manager.toggle_first_point_gender()

        assert gender_manager.get_next_retry_delay() == 1.0

        with patch.object(
            network_manager,
            "set_first_point_gender",
            side_effect=Exception("Network error"),
        ):
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 2.0

            gender_manager.reset_sync_timing()
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 4.0

            gender_manager.reset_sync_timing()
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 8.0

            gender_manager.reset_sync_timing()
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 16.0

            gender_manager.reset_sync_timing()
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 32.0

            gender_manager.reset_sync_timing()
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 60.0

            gender_manager.reset_sync_timing()
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 60.0

    @pytest.mark.asyncio
    async def test_backoff_resets_after_successful_sync(
        self, gender_manager, network_manager
    ):
        """Test that backoff delay resets after a successful sync."""
        gender_manager.toggle_first_point_gender()

        with patch.object(
            network_manager,
            "set_first_point_gender",
            side_effect=Exception("Network error"),
        ):
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 2.0

            gender_manager.reset_sync_timing()
            await gender_manager.try_sync_gender()
            assert gender_manager.get_next_retry_delay() == 4.0

        gender_manager.toggle_first_point_gender()
        gender_manager.reset_sync_timing()
        success = await gender_manager.try_sync_gender()
        assert success
        assert gender_manager.get_next_retry_delay() == 1.0

    @pytest.mark.asyncio
    async def test_concurrent_local_and_network_updates(
        self, gender_manager, fake_matrix_portal, network_manager
    ):
        """Test behavior when local changes are made while network has different values."""
        fake_matrix_portal.set_feed_value(NetworkManager.FIRST_POINT_GENDER_FEED, "wmp")

        gender_manager.toggle_first_point_gender()
        assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP
        assert gender_manager.has_pending_changes()

        with patch.object(
            network_manager,
            "set_first_point_gender",
            side_effect=Exception("Network error"),
        ):
            changed = await gender_manager.update_gender_from_network()
            assert not changed
            assert gender_manager.get_first_point_gender() == GenderManager.GENDER_MMP

        gender_manager.reset_sync_timing()
        success = await gender_manager.try_sync_gender()
        assert success
        assert not gender_manager.has_pending_changes()

    @pytest.mark.asyncio
    async def test_retry_delay_prevents_immediate_retry(
        self, gender_manager, network_manager
    ):
        """Test that retry delay prevents sync attempts before delay expires."""
        gender_manager.toggle_first_point_gender()

        with patch.object(
            network_manager,
            "set_first_point_gender",
            side_effect=Exception("Network error"),
        ):
            result1 = await gender_manager.try_sync_gender()
            assert not result1

            result2 = await gender_manager.try_sync_gender()
            assert not result2

            assert gender_manager.has_pending_changes()
