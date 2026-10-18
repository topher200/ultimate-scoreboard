"""Tests for OtaManager."""

import json

import pytest

import ota_loader
from fakes import FakeHttp, FakeResponse
from src.bundle import pack
from src.ota_manager import LATEST_URL, DeviceInfo, OtaManager

DOWNLOAD_URL = "https://example.com/scoreboard-1.1.0.bundle"
BUNDLE_FILES = {"src/board_main.py": b"VERSION = 2\n"}


@pytest.fixture
def root(tmp_path):
    return f"{tmp_path}/"


@pytest.fixture
def fake_http():
    return FakeHttp()


@pytest.fixture
def resets():
    return []


@pytest.fixture
def ota_manager(fake_http, display_manager, root, resets):
    device = DeviceInfo("abc123", "matrixportal-s3", "scoreboard", "1.0.0")
    return OtaManager(
        fake_http,
        "project-key",
        device,
        display_manager,
        root,
        lambda: resets.append(1),
    )


def offer_update(fake_http, bundle: bytes, version: str = "1.1.0") -> None:
    release = {"version": version, "artifacts": [{"url": DOWNLOAD_URL}]}
    fake_http.responses[LATEST_URL] = FakeResponse(200, json.dumps(release).encode())
    fake_http.responses[DOWNLOAD_URL] = FakeResponse(200, bundle)


class TestCheckAndInstall:
    def test_check_sends_the_device_and_the_project_key(self, ota_manager, fake_http):
        fake_http.responses[LATEST_URL] = FakeResponse(204)

        ota_manager.check_and_install()

        url, headers = fake_http.requests[0]
        assert "device_serial=abc123" in url
        assert "hardware_version=matrixportal-s3" in url
        assert "software_type=scoreboard" in url
        assert "current_version=1.0.0" in url
        assert headers == {"Memfault-Project-Key": "project-key"}

    def test_up_to_date_ends_the_trial(self, ota_manager, fake_http, root, resets):
        ota_loader.start_trial(root, "a", "1.0.0")
        fake_http.responses[LATEST_URL] = FakeResponse(204)

        ota_manager.check_and_install()

        assert not ota_loader.in_trial(root)
        assert resets == []

    def test_failed_check_keeps_the_trial(self, ota_manager, fake_http, root):
        ota_loader.start_trial(root, "a", "1.0.0")
        fake_http.responses[LATEST_URL] = FakeResponse(500)

        ota_manager.check_and_install()

        assert ota_loader.in_trial(root)

    def test_update_installs_into_the_inactive_slot_and_resets(
        self, ota_manager, fake_http, root, resets, display_manager
    ):
        ota_loader.start_trial(root, "a", "1.0.0")
        offer_update(fake_http, pack(BUNDLE_FILES))

        ota_manager.check_and_install()

        assert resets == [1]
        assert ota_loader.app_path(root) == f"{root}slots/b"
        assert ota_loader.in_trial(root)
        assert ota_loader.read_state(root)[ota_loader.VERSION] == "1.1.0"
        with open(f"{root}slots/b/src/board_main.py", "rb") as f:
            assert f.read() == BUNDLE_FILES["src/board_main.py"]
        assert display_manager.update_notice_shown

    def test_damaged_download_keeps_the_running_slot(
        self, ota_manager, fake_http, root, resets, display_manager
    ):
        ota_loader.start_trial(root, "a", "1.0.0")
        ota_loader.mark_healthy(root)
        offer_update(fake_http, pack(BUNDLE_FILES)[:-1])

        ota_manager.check_and_install()

        assert resets == []
        assert ota_loader.app_path(root) == f"{root}slots/a"
        assert not display_manager.update_notice_shown

    def test_skips_a_release_that_crashed_during_its_trial(
        self, ota_manager, fake_http, root, resets
    ):
        ota_loader.start_trial(root, "a", "1.1.0")
        ota_loader.roll_back_trial(root)
        offer_update(fake_http, pack(BUNDLE_FILES), version="1.1.0")

        ota_manager.check_and_install()

        assert resets == []
        assert len(fake_http.requests) == 1

    def test_installs_a_newer_release_after_a_rollback(
        self, ota_manager, fake_http, root, resets
    ):
        ota_loader.start_trial(root, "a", "1.1.0")
        ota_loader.roll_back_trial(root)
        offer_update(fake_http, pack(BUNDLE_FILES), version="1.2.0")

        ota_manager.check_and_install()

        assert resets == [1]

    def test_check_in_that_cannot_write_the_state_does_not_raise(
        self, ota_manager, fake_http, root, mocker
    ):
        ota_loader.start_trial(root, "a", "1.0.0")
        mocker.patch.object(ota_loader, "write_state", side_effect=OSError("read-only"))
        fake_http.responses[LATEST_URL] = FakeResponse(204)

        ota_manager.check_and_install()
