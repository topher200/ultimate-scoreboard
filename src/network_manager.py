"""Joins Wi-Fi and serves the settings page."""

from __future__ import annotations

import asyncio

from src.compat import TYPE_CHECKING, Callable
from src.protocols import NetworkLike, WebServerLike

if TYPE_CHECKING:
    from src.display_manager import DisplayManager

SETTINGS_PAGE_PORT = 8080
ACCESS_POINT_SSID = "Scoreboard"
# Phone cameras offer to join the Wi-Fi network in this QR code
ACCESS_POINT_QR_CODE_TEXT = f"WIFI:T:nopass;S:{ACCESS_POINT_SSID};;"
SERVER_POLL_INTERVAL = 0.1


class NetworkManager:
    """Joins Wi-Fi, serves the settings page, and shows its QR code.

    When the board cannot join the Wi-Fi in settings.toml, it hosts an open
    access point instead. The QR code then joins a phone to the access point,
    and changes to the page URL once a device joins.

    Joining Wi-Fi is synchronous and blocks the event loop until it finishes.
    """

    def __init__(
        self,
        network: NetworkLike,
        display_manager: DisplayManager,
        web_server: WebServerLike,
        respond: Callable,
    ):
        """Initialize NetworkManager.

        :param network: Network that joins Wi-Fi or hosts an access point
        :param display_manager: DisplayManager for the connecting dot and QR code
        :param web_server: Server for the settings page
        :param respond: Request handler for the settings page; see WebServerLike.start
        """
        self._network = network
        self._display_manager = display_manager
        self._web_server = web_server
        self._respond = respond
        self._url: str | None = None
        self._waiting_for_access_point_client = False

    @property
    def url(self) -> str | None:
        """URL of the settings page, or None until the server starts."""
        return self._url

    def connect(self) -> None:
        """Join Wi-Fi or host an access point, start the settings page, and show a QR code.

        Does nothing once the settings page is up.
        """
        if self._url is not None:
            return
        self._display_manager.show_connecting(True)
        try:
            host = self._join_or_host_wifi()
            self._url = self._web_server.start(host, SETTINGS_PAGE_PORT, self._respond)
        except Exception as e:
            print(f"Failed to start the settings page: {e}")
            self._waiting_for_access_point_client = False
            return
        finally:
            self._display_manager.show_connecting(False)
        print(f"Settings page: {self._url}")
        if self._waiting_for_access_point_client:
            self._display_manager.show_qr_code(ACCESS_POINT_QR_CODE_TEXT)
        else:
            self._display_manager.show_qr_code(self._url)

    def _join_or_host_wifi(self) -> str:
        """Join the Wi-Fi in settings.toml, or host an access point if that fails.

        :return: The board's IP address
        """
        try:
            return self._network.connect()
        except Exception as e:
            print(f"Failed to join Wi-Fi: {e}")
        print(f"Hosting Wi-Fi network {ACCESS_POINT_SSID}")
        host = self._network.start_access_point(ACCESS_POINT_SSID)
        self._waiting_for_access_point_client = True
        return host

    def _show_url_once_a_device_joins(self) -> None:
        """Swap the access point QR code for the page URL when a device joins."""
        if not self._waiting_for_access_point_client:
            return
        if not self._display_manager.qr_code_shown:
            self._waiting_for_access_point_client = False
            return
        if self._network.access_point_has_clients():
            self._waiting_for_access_point_client = False
            assert self._url is not None
            self._display_manager.show_qr_code(self._url)

    async def serve(self) -> None:
        """Answer settings page requests forever."""
        while True:
            if self._url is not None:
                try:
                    self._show_url_once_a_device_joins()
                    self._web_server.poll()
                except Exception as e:
                    print(f"Settings page request failed: {e}")
            await asyncio.sleep(SERVER_POLL_INTERVAL)
