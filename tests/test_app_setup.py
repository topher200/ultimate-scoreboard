"""Tests for app_setup helpers."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from src import button_state_machine
from src.app_setup import (
    create_managers,
    dismiss_qr_code_first,
    initialize_application,
    run_tasks,
)
from src.display_manager import LEFT_TEAM, RIGHT_TEAM
from src.hardware_manager import KEY_NUMBER_BUTTON_LEFT, KEY_NUMBER_BUTTON_RIGHT
from src.settings_store import LEFT_TEAM_NAME, RIGHT_TEAM_NAME, SettingsStore


class TestDismissQrCodeFirst:
    async def test_press_while_qr_code_shows_only_hides_it(self, display_manager):
        callback = AsyncMock()
        display_manager.show_qr_code("http://192.168.1.50:8080/")

        await dismiss_qr_code_first(display_manager, callback)()

        assert not display_manager.qr_code_shown
        callback.assert_not_called()

    async def test_press_without_qr_code_runs_callback(self, display_manager):
        callback = AsyncMock()

        await dismiss_qr_code_first(display_manager, callback)()

        callback.assert_awaited_once()


class TestInitializeApplication:
    def test_checks_for_update_after_wifi_joins(
        self, fake_matrix_portal, fake_keys, fake_network, fake_web_server
    ):
        managers = create_managers(
            fake_matrix_portal, fake_keys, bytearray(256), fake_network, fake_web_server
        )
        ota_manager = Mock()

        initialize_application(managers, ota_manager)

        ota_manager.check_and_install.assert_called_once()

    def test_skips_update_check_without_wifi(
        self, fake_matrix_portal, fake_keys, fake_network, fake_web_server
    ):
        fake_network.connect_error = OSError("no network")
        managers = create_managers(
            fake_matrix_portal, fake_keys, bytearray(256), fake_network, fake_web_server
        )
        ota_manager = Mock()

        initialize_application(managers, ota_manager)

        ota_manager.check_and_install.assert_not_called()

    def test_uploads_telemetry_before_the_update_check(
        self, fake_matrix_portal, fake_keys, fake_network, fake_web_server
    ):
        managers = create_managers(
            fake_matrix_portal, fake_keys, bytearray(256), fake_network, fake_web_server
        )
        calls = Mock()

        initialize_application(managers, calls.ota_manager, calls.telemetry)

        assert [c[0] for c in calls.mock_calls] == [
            "telemetry.flush",
            "ota_manager.check_and_install",
        ]

    def test_skips_telemetry_upload_without_wifi(
        self, fake_matrix_portal, fake_keys, fake_network, fake_web_server
    ):
        fake_network.connect_error = OSError("no network")
        managers = create_managers(
            fake_matrix_portal, fake_keys, bytearray(256), fake_network, fake_web_server
        )
        telemetry = Mock()

        initialize_application(managers, None, telemetry)

        telemetry.flush.assert_not_called()


class TestCreateManagers:
    def test_boot_shows_saved_names_and_saving_applies_new_ones(
        self, fake_matrix_portal, fake_keys, fake_network, fake_web_server
    ):
        nvm = bytearray(256)
        SettingsStore(nvm).save({LEFT_TEAM_NAME: "Phoenix", RIGHT_TEAM_NAME: "Tigers"})
        managers = create_managers(
            fake_matrix_portal, fake_keys, nvm, fake_network, fake_web_server
        )

        initialize_application(managers)

        labels = managers.display_manager._labels
        assert labels[LEFT_TEAM].text == "Phoenix"
        assert managers.display_manager.qr_code_shown

        fake_web_server.respond({LEFT_TEAM_NAME: "Fury", RIGHT_TEAM_NAME: "Riot"})

        assert labels[LEFT_TEAM].text == "Fury"
        assert labels[RIGHT_TEAM].text == "Riot"
        assert not managers.display_manager.qr_code_shown


class TestRunTasksGestures:
    """Drive the whole app through fake keys."""

    @pytest.fixture
    def app(
        self, monkeypatch, fake_matrix_portal, fake_keys, fake_network, fake_web_server
    ):
        monkeypatch.setattr(button_state_machine, "SIMULTANEOUS_HOLD_THRESHOLD", 0.2)
        managers = create_managers(
            fake_matrix_portal, fake_keys, bytearray(256), fake_network, fake_web_server
        )
        initialize_application(managers)
        return managers

    async def _tap(self, keys, *key_numbers, hold=0.05):
        for key_number in key_numbers:
            keys.press_key(key_number)
        await asyncio.sleep(hold)
        for key_number in key_numbers:
            keys.release_key(key_number)
        await asyncio.sleep(0.15)

    async def test_first_press_hides_qr_code_then_hold_both_resets(
        self, app, fake_keys
    ):
        task = asyncio.create_task(run_tasks(app))
        try:
            assert app.display_manager.qr_code_shown

            await self._tap(fake_keys, KEY_NUMBER_BUTTON_LEFT)
            assert not app.display_manager.qr_code_shown
            assert app.score_manager.left_score == 0

            await self._tap(fake_keys, KEY_NUMBER_BUTTON_LEFT)
            await self._tap(fake_keys, KEY_NUMBER_BUTTON_LEFT)
            assert app.score_manager.left_score == 2

            await self._tap(
                fake_keys, KEY_NUMBER_BUTTON_LEFT, KEY_NUMBER_BUTTON_RIGHT, hold=0.4
            )
            assert app.score_manager.left_score == 0
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
