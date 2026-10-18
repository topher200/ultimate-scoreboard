"""Protocol definitions for the Wi-Fi network and web server."""

from src.compat import Callable, Protocol


class NetworkLike(Protocol):
    """Protocol defining the Wi-Fi interface used in this project."""

    def connect(self) -> str:
        """Join the Wi-Fi network in settings.toml.

        :return: The board's IP address on that network
        :raises OSError: If the board cannot join
        """
        ...

    def start_access_point(self, ssid: str) -> str:
        """Start an open Wi-Fi network for phones to join.

        :param ssid: Name of the network
        :return: The board's IP address on that network
        """
        ...

    def access_point_has_clients(self) -> bool:
        """True when a device has joined the access point."""
        ...


class WebServerLike(Protocol):
    """Protocol defining the settings page server."""

    def start(self, host: str, port: int, respond: Callable) -> str:
        """Start serving.

        :param host: IP address of the board, which the URL uses
        :param port: TCP port to listen on
        :param respond: Called with the submitted form dict, or None for a
            plain page view; returns the page HTML
        :return: URL of the page
        """
        ...

    def poll(self) -> None:
        """Handle a waiting request, if there is one."""
        ...
