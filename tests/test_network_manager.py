"""Tests for NetworkManager using fake implementations."""

import asyncio
from unittest.mock import MagicMock

import pytest

from fakes import FakeNetwork
from src.network_manager import SETTINGS_PAGE_PORT
from tests.qr_code import shows_qr_code

URL = f"http://{FakeNetwork.IP_ADDRESS}:{SETTINGS_PAGE_PORT}/"


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

    def test_wifi_search_shows_only_while_joining(
        self, network_manager, display_manager, fake_network
    ):
        shown_while_joining = []
        connect = fake_network.connect

        def connect_and_record():
            shown_while_joining.append(display_manager.wifi_search_shown)
            return connect()

        fake_network.connect = connect_and_record

        network_manager.connect()

        assert shown_while_joining == [True]
        assert not display_manager.wifi_search_shown

    def test_failed_join_shows_no_qr_code_and_can_retry(
        self, network_manager, display_manager, fake_network
    ):
        fake_network.connect_error = OSError("no Wi-Fi")

        network_manager.connect()

        assert network_manager.url is None
        assert not display_manager.qr_code_shown

        fake_network.connect_error = None
        network_manager.connect()

        assert shows_qr_code(display_manager, URL)

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
