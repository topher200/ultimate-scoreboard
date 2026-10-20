"""Serves the settings page over the board's Wi-Fi connection."""

import wifi
from adafruit_connection_manager import get_radio_socketpool
from adafruit_httpserver import GET, POST, Redirect, Request, Response, Server

from src.protocols import PageLike
from src.settings_page import SAVED_PATH, decode_form

# Seconds the server waits on a connection that sends nothing
SOCKET_TIMEOUT = 0.2


class WebServer:
    """Serves one page at "/" with adafruit_httpserver."""

    def __init__(self):
        self._server: Server | None = None

    def start(self, host: str, port: int, page: PageLike) -> str:
        """Start serving.

        :param host: IP address of the board, which the URL uses
        :param port: TCP port to listen on
        :param page: Page to serve at "/"; see WebServerLike.start
        :return: URL of the page
        """
        server = Server(get_radio_socketpool(wifi.radio))
        server.socket_timeout = SOCKET_TIMEOUT

        @server.route("/", [GET, POST])
        def handle(request: Request) -> Response:
            if request.method == POST:
                if request.form_data is not None:
                    page.save(decode_form(request.form_data))
                return Redirect(request, SAVED_PATH, status=(303, "See Other"))
            saved = request.query_params.get("saved") == "1"
            return Response(request, page.render(saved), content_type="text/html")

        server.start(host, port)
        self._server = server
        return f"http://{host}:{port}/"

    def poll(self) -> None:
        """Handle a waiting request, if there is one."""
        if self._server is not None:
            self._server.poll()
