"""Tests for app_setup helpers."""

from unittest.mock import AsyncMock

from src.app_setup import (
    create_managers,
    dismiss_qr_code_first,
    initialize_application,
)
from src.display_manager import LEFT_TEAM, RIGHT_TEAM
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
