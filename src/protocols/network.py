"""Protocol definitions for the Wi-Fi network and web server."""

from src.compat import Protocol


class NetworkLike(Protocol):
    """Protocol defining the Wi-Fi interface used in this project."""

    def connect(self) -> str:
        """Join the Wi-Fi network in settings.toml.

        :return: The board's IP address on that network
        :raises OSError: If the board cannot join
        """
        ...


class PageLike(Protocol):
    """Protocol defining the page that a WebServerLike serves."""

    def save(self, form: dict) -> None:
        """Save the submitted form dict."""
        ...

    def render(self, saved: bool = False) -> str:
        """Return the page HTML, with a note that the last submit saved."""
        ...


class WebServerLike(Protocol):
    """Protocol defining the settings page server."""

    def start(self, host: str, port: int, page: PageLike) -> str:
        """Start serving.

        A submit saves the form, then redirects the browser to settings_page.SAVED_PATH so
        that a reload does not submit again.

        :param host: IP address of the board, which the URL uses
        :param port: TCP port to listen on
        :param page: Page to serve at "/"
        :return: URL of the page
        """
        ...

    def poll(self) -> None:
        """Handle a waiting request, if there is one."""
        ...
