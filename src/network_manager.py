"""Joins Wi-Fi and serves the settings page."""

from __future__ import annotations

import asyncio

from src.compat import TYPE_CHECKING
from src.log import WARNING, log
from src.protocols import NetworkLike, PageLike, WebServerLike

if TYPE_CHECKING:
    from src.display_manager import DisplayManager

SETTINGS_PAGE_PORT = 8080
SERVER_POLL_INTERVAL = 0.1


class NetworkManager:
    """Joins Wi-Fi, serves the settings page, and shows its QR code.

    Joining Wi-Fi is synchronous and blocks the event loop until it finishes.
    """

    def __init__(
        self,
        network: NetworkLike,
        display_manager: DisplayManager,
        web_server: WebServerLike,
        page: PageLike,
    ):
        """Initialize NetworkManager.

        :param network: Network that joins the Wi-Fi in settings.toml
        :param display_manager: DisplayManager for the Wi-Fi search screen and QR code
        :param web_server: Server for the settings page
        :param page: Settings page to serve
        """
        self._network = network
        self._display_manager = display_manager
        self._web_server = web_server
        self._page = page
        self._url: str | None = None

    @property
    def url(self) -> str | None:
        """URL of the settings page, or None until the server starts."""
        return self._url

    def connect(self) -> None:
        """Join Wi-Fi, start the settings page, and show its QR code.

        Does nothing once the settings page is up.
        """
        if self._url is not None:
            return
        self._display_manager.show_wifi_search()
        try:
            host = self._network.connect()
            self._url = self._web_server.start(host, SETTINGS_PAGE_PORT, self._page)
        except Exception as e:
            log(f"Failed to start the settings page: {e}", WARNING)
            return
        finally:
            self._display_manager.hide_wifi_search()
        log(f"Settings page: {self._url}")
        self._display_manager.show_qr_code(self._url)

    async def serve(self) -> None:
        """Answer settings page requests forever."""
        while True:
            if self._url is not None:
                try:
                    self._web_server.poll()
                except Exception as e:
                    log(f"Settings page request failed: {e}", WARNING)
            await asyncio.sleep(SERVER_POLL_INTERVAL)
