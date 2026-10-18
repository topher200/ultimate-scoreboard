"""Tests for NetworkManager using fake implementations."""

import asyncio
from unittest.mock import MagicMock

import pytest

from fakes import FakeNetwork
from src.network_manager import (
    ACCESS_POINT_QR_CODE_TEXT,
    ACCESS_POINT_SSID,
    SETTINGS_PAGE_PORT,
)
from tests.qr_code import shows_qr_code

URL = f"http://{FakeNetwork.IP_ADDRESS}:{SETTINGS_PAGE_PORT}/"
ACCESS_POINT_URL = f"http://{FakeNetwork.ACCESS_POINT_IP_ADDRESS}:{SETTINGS_PAGE_PORT}/"


async def _serve_briefly(network_manager):
    task = asyncio.create_task(network_manager.serve())
    await asyncio.sleep(0.25)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


class TestNetworkManagerConnect:
    def test_connect_starts_settings_page_and_shows_its_qr_code(
        self, network_manager, display_manager, fake_web_server
    ):
        network_manager.connect()

        assert fake_web_server.host == FakeNetwork.IP_ADDRESS
        assert network_manager.url == URL
        assert shows_qr_code(display_manager, URL)

    def test_connect_does_nothing_once_settings_page_is_up(
        self, network_manager, fake_network
    ):
        network_manager.connect()
        network_manager.connect()

        assert fake_network.connect_count == 1

    def test_show_connecting_brackets_connect(self, network_manager, display_manager):
        display_manager.show_connecting = MagicMock()

        network_manager.connect()

        assert [c.args for c in display_manager.show_connecting.call_args_list] == [
            (True,),
            (False,),
        ]

    def test_failed_server_start_shows_no_qr_code_and_can_retry(
        self, network_manager, display_manager, fake_web_server
    ):
        start = fake_web_server.start
        fake_web_server.start = MagicMock(side_effect=OSError("in use"))

        network_manager.connect()

        assert network_manager.url is None
        assert not display_manager.qr_code_shown

        fake_web_server.start = start
        network_manager.connect()

        assert network_manager.url == URL


class TestNetworkManagerAccessPoint:
    @pytest.fixture(autouse=True)
    def no_wifi(self, fake_network):
        fake_network.connect_error = OSError("no Wi-Fi")

    def test_failed_join_hosts_access_point(
        self, network_manager, fake_network, fake_web_server
    ):
        network_manager.connect()

        assert fake_network.access_point_ssid == ACCESS_POINT_SSID
        assert fake_web_server.host == FakeNetwork.ACCESS_POINT_IP_ADDRESS
        assert network_manager.url == ACCESS_POINT_URL

    def test_shows_wifi_qr_code_until_a_device_joins(
        self, network_manager, display_manager
    ):
        network_manager.connect()

        assert shows_qr_code(display_manager, ACCESS_POINT_QR_CODE_TEXT)

    async def test_shows_url_qr_code_after_a_device_joins(
        self, network_manager, display_manager, fake_network
    ):
        network_manager.connect()
        await _serve_briefly(network_manager)
        assert shows_qr_code(display_manager, ACCESS_POINT_QR_CODE_TEXT)

        fake_network.access_point_clients = 1
        await _serve_briefly(network_manager)

        assert shows_qr_code(display_manager, ACCESS_POINT_URL)

    async def test_dismissed_qr_code_stays_hidden_after_a_device_joins(
        self, network_manager, display_manager, fake_network
    ):
        network_manager.connect()
        display_manager.hide_qr_code()

        fake_network.access_point_clients = 1
        await _serve_briefly(network_manager)

        assert not display_manager.qr_code_shown


class TestNetworkManagerServe:
    async def test_serve_polls_only_after_connect(
        self, network_manager, fake_web_server
    ):
        await _serve_briefly(network_manager)
        assert fake_web_server.poll_count == 0

        network_manager.connect()
        await _serve_briefly(network_manager)
        assert fake_web_server.poll_count > 0

    async def test_serve_survives_a_failed_request(
        self, network_manager, fake_web_server
    ):
        fake_web_server.poll = MagicMock(side_effect=OSError("reset"))
        network_manager.connect()

        await _serve_briefly(network_manager)

        assert fake_web_server.poll.call_count > 1
